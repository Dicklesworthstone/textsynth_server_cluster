import httpx
import asyncio
import logging
from itertools import cycle
import ipaddress
import time
import yaml
import configparser
import random
import json
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONCURRENT_REQUESTS = 50  # Adjust as needed
RETRY_COUNT = 2  # Adjust as needed
TIMEOUT_FOR_INFERENCE_IN_SECONDS = 60.0  # Adjust as needed
MAX_TOKENS_IN_RESPONSE = 100  # Adjust as needed
TS_SERVER_LISTEN_PORT = 8088 #If you change this, you'll need to change the port in the TS server's config file in the `run_ts_server_with_llama2_13b_chat_on_ubuntu.sh` script.
file_path_to_ansible_inventory_file = 'my_ansible_inventory_for_ts_server_cluster.yml'


def extract_ips_from_ansible_inventory(inventory_filepath, output_filepath='list_of_ts_server_ips.txt'):
    logger.info(f"Extracting IP addresses from {inventory_filepath}...")
    ips = []
    if inventory_filepath.endswith('.yml') or inventory_filepath.endswith('.yaml'):
        with open(inventory_filepath, 'r') as file:
            inventory_data = yaml.safe_load(file)
        for host_data in inventory_data.get('all', {}).get('hosts', {}).values():
            ip = host_data.get('ansible_host')
            if ip:
                ips.append(ip)
    elif inventory_filepath.endswith('.ini'):
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(inventory_filepath)
        for section in config.sections():
            for key in config[section]:
                ip = key.split(' ')[0].split(':')[0]
                ips.append(ip)
    else:
        raise ValueError("Unsupported file format. Please provide a YAML or INI file.")
    with open(output_filepath, 'w') as file:
        file.write('\n'.join(ips))
    logger.info(f"IP addresses extracted to {output_filepath}")


def validate_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


async def check_ip_availability(client, ip, port=TS_SERVER_LISTEN_PORT):
    if not validate_ip(ip):
        logger.warning(f"IP {ip} is not a valid IP address and will be excluded from the request list.")
        return None
    url = f"http://{ip}:{TS_SERVER_LISTEN_PORT}/"
    try:
        response = await client.get(url)
        return ip if response.status_code == 200 else None
    except (httpx.HTTPError, httpx.ReadTimeout):
        return None
    

async def test_single_server(client, ip, prompt, timeout, max_tokens=10):
    url = f"http://{ip}:{TS_SERVER_LISTEN_PORT}/v1/engines/llama2_13B_chat/completions"
    data = {"prompt": prompt, "max_tokens": max_tokens}
    headers = {"Content-Type": "application/json"}
    try:
        response = await client.post(url, json=data, headers=headers, timeout=timeout)
        completion_time = response.elapsed.total_seconds()
        return {
            "completion_time": completion_time,
            "response": response.json()
        }
    except (httpx.HTTPError, httpx.ReadTimeout) as e:
        logger.warning(f"Request to {ip} failed for prompt: {prompt}. Error: {e}")
        return None


async def test_ts_servers():
    prompt = "Respond to this question:\n The capital of France is:\n"
    timeout = httpx.Timeout(TIMEOUT_FOR_INFERENCE_IN_SECONDS, connect=5.0)  # Adjust as needed
    results = {}
    async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=2.0)) as client:
        with open('list_of_ts_server_ips.txt', 'r') as f:
            ip_addresses = f.read().splitlines()
        for ip in ip_addresses:
            if not validate_ip(ip):
                logger.warning(f"IP {ip} is not a valid IP address and will be excluded from the test.")
                continue
            result = await test_single_server(client, ip, prompt, timeout)
            if result:
                results[ip] = result
    return results


async def send_request(client, ip, prompt, semaphore, retries=RETRY_COUNT):
    async with semaphore:
        logger.info(f"Sending request to {ip}:{TS_SERVER_LISTEN_PORT} for prompt: {prompt}. Retries remaining: {retries}")
        url = f"http://{ip}:{TS_SERVER_LISTEN_PORT}/v1/engines/llama2_13B_chat/completions"
        data = {"prompt": prompt, "max_tokens": MAX_TOKENS_IN_RESPONSE}
        headers = {"Content-Type": "application/json"}
        timeout = httpx.Timeout(TIMEOUT_FOR_INFERENCE_IN_SECONDS, connect=5.0)  # Adjust as needed
        try:
            response = await client.post(url, json=data, headers=headers, timeout=timeout)
            logger.info(f"Received response from {ip}:{TS_SERVER_LISTEN_PORT} for prompt: {prompt}")
            return prompt, response.json()
        except (httpx.HTTPError, httpx.ReadTimeout) as e:
            logger.warning(f"Request to {ip}:{TS_SERVER_LISTEN_PORT} failed for prompt: {prompt}. Error: {str(e)}")
            if retries > 0:
                return await send_request(client, ip, prompt, semaphore, retries - 1)
            logger.error(f"Failed to get response from {ip}:{TS_SERVER_LISTEN_PORT} for prompt: {prompt} after all retries.")
            return prompt, None


async def process_requests(client, ip_iterator, semaphore, prompt_queue, results):
    logger.info("Starting a process_requests worker...")
    while True:
        prompt = await prompt_queue.get()
        if prompt is None:
            logger.info("Received a None prompt, ending this worker.")
            break
        ip = next(ip_iterator)
        logger.info(f"Processing prompt: {prompt} on IP: {ip}:{TS_SERVER_LISTEN_PORT}")
        prompt, result = await send_request(client, ip, prompt, semaphore)
        if result:
            results[prompt] = result
            logger.info(f"Saved result for prompt: {prompt}")
        else:
            logger.warning(f"No result received for prompt: {prompt}")
        prompt_queue.task_done()
        logger.info(f"Finished processing prompt: {prompt}")
    logger.info("Ending process_requests worker.")


async def round_robin_request(prompts):
    logger.info("Starting round-robin request processing...")
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
    async with httpx.AsyncClient(timeout=httpx.Timeout(TIMEOUT_FOR_INFERENCE_IN_SECONDS, connect=2.0)) as client:
        # Check IP availability
        with open('list_of_ts_server_ips.txt', 'r') as f:
            ip_addresses = f.read().splitlines()
        ip_check_tasks = [check_ip_availability(client, ip, TS_SERVER_LISTEN_PORT) for ip in ip_addresses]
        live_ips = [ip for ip in await asyncio.gather(*ip_check_tasks) if ip]
        non_responsive_ips = set(ip_addresses) - set(live_ips)
        for ip in non_responsive_ips:
            logger.warning(f"IP {ip}:{TS_SERVER_LISTEN_PORT} is not responding and will be excluded from the request list.")
        results = {}
        ip_iterator = cycle(live_ips)
        prompt_queue = asyncio.Queue()
        for prompt in prompts:
            await prompt_queue.put(prompt)
        logger.info(f"Added {len(prompts)} prompts to the queue.")
        worker_tasks = [process_requests(client, ip_iterator, semaphore, prompt_queue, results)
                        for _ in range(CONCURRENT_REQUESTS)]
        await prompt_queue.join()
        for _ in range(CONCURRENT_REQUESTS):
            await prompt_queue.put(None)
        await asyncio.gather(*worker_tasks)
    logger.info("Round-robin request processing completed.")
    return results


def generate_movie_synopsis_prompt(movie_title: str) -> str:
    template = f"""
    Please provide a short synopsis of the plot of the movie "{movie_title}." Keep it concise and focused on the main storyline.

    Response: The synopsis of "{movie_title}" is:
    """
    return template


def generate_movie_synopsis_prompts():
    list_of_prompts = []
    for movie_title in MOVIE_TITLES:
        current_prompt = generate_movie_synopsis_prompt(movie_title)
        list_of_prompts.append(current_prompt)
    return list_of_prompts


def generate_movie_details_prompt(movie_title: str, random_seed: int) -> str:
    template = f"""
    Random Seed: {random_seed}
    
    Please provide details of the movie "{movie_title}" in the form of a JSON object with the following keys:
    - "title": Title of the movie
    - "release_year": Year the movie was released
    - "director": Name of the director
    - "genre": Genre of the movie
    - "main_actors": List of main actors

    Response: The details of "{movie_title}" are:
    """
    return template


def generate_movie_details_prompts():
    list_of_prompts = []
    for movie_title in MOVIE_TITLES:
        random_seed = random.randint(0, 255)
        current_prompt = generate_movie_details_prompt(movie_title, random_seed)
        list_of_prompts.append(current_prompt)
    return list_of_prompts


def validate_and_correct_json(response: str) -> tuple:
    # Attempt to remove common issues that might prevent JSON validation
    corrected_response = response.strip("` '\"")  # Remove backticks, quotes, and extra spaces
    # Try to parse the corrected JSON
    try:
        json_data = json.loads(corrected_response)
        return True, json_data
    except json.JSONDecodeError:
        return False, None
    

async def get_movie_details(movie_title: str):
    max_retries = 5  # Maximum number of retries
    retries = 0
    while retries < max_retries:
        random_seed = random.randint(0, 255)
        prompt = generate_movie_details_prompt(movie_title, random_seed)
        # Sending the prompt to the model using the existing round-robin request function
        results = await round_robin_request([prompt])
        # Getting the response from the results
        model_response_text = results[prompt]["response"]["choices"][0]["text"]
        # Validate and correct the JSON response
        is_valid, json_data = validate_and_correct_json(model_response_text)
        if is_valid:
            return json_data
        retries += 1
    raise Exception("Max retries reached. Unable to parse valid JSON.")


def extract_movie_title_from_prompt(prompt: str) -> str:
    logger.info(f"Extracting movie title from prompt: {prompt}")
    match = re.search(r'\"(.*?)\"', prompt)
    title = match.group(1) if match else None
    logger.info(f"Extracted movie title: {title}")
    return title


async def get_all_movie_details():
    logger.info("Generating movie details prompts...")
    movie_details_prompts = generate_movie_details_prompts()
    logger.info("Sending movie details prompts to ts servers...")
    results = await round_robin_request(movie_details_prompts)
    movie_details = {}  # Dictionary to store the final details for each movie
    logger.info("Processing results from ts servers...")
    for prompt, result in results.items():  # Iterate through the results and validate the JSON
        if result:
            model_response_text = result["response"]["choices"][0]["text"]
            is_valid, json_data = validate_and_correct_json(model_response_text)
            if is_valid:
                movie_title = extract_movie_title_from_prompt(prompt)  # Function to get movie title from prompt
                movie_details[movie_title] = json_data
                logger.info(f"Saved movie details for: {movie_title}")
            else:
                logger.warning(f"Invalid JSON response for prompt: {prompt}")
        else:
            logger.warning(f"No result received for prompt: {prompt}")
    logger.info("Finished processing all movie details.")
    return movie_details


if __name__ == "__main__":
    MOVIE_TITLES = ["Forrest Gump", "The Shawshank Redemption", "The Godfather", "The Dark Knight",
    "Titanic", "Pulp Fiction", "Gladiator", "The Matrix", "Fight Club", "Inception",
    "Avatar", "The Lord of the Rings: The Return of the King", "Star Wars: Episode IV - A New Hope",
    "Jurassic Park", "The Lion King", "Toy Story", "Harry Potter and the Sorcerer's Stone",
    "Frozen", "Shrek", "Spider-Man"]

    try:
        extract_ips_from_ansible_inventory(file_path_to_ansible_inventory_file)
        use_test_ts_servers = 0
        if use_test_ts_servers:
            test_results = asyncio.run(test_ts_servers())
            logger.info(test_results)
            with open('ts_server_test_results.json', 'w') as f:
                f.write(json.dumps(test_results, indent=4))
        logger.info(f"Generating prompts for movie synopsis task for {len(MOVIE_TITLES)} movies...")
        list_of_prompts = generate_movie_synopsis_prompts()
        logger.info(f"Sending {len(list_of_prompts)} prompts to the ts servers...")
        results = asyncio.run(round_robin_request(list_of_prompts))
        output_file_name = 'movie_synopsis_results_from_ts_servers.json'
        with open(output_file_name, 'w') as f:
            f.write(json.dumps(results, indent=4))
        logger.info(f"Synopsis Results written to {output_file_name}")
            
        logger.info(f"Now getting movie details JSON responses for {len(MOVIE_TITLES)} movies on the ts servers...")
        all_movie_details = asyncio.run(get_all_movie_details())
        output_file_name = 'movie_details_results_from_ts_servers.json'
        with open(output_file_name, 'w') as f:
            json.dump(all_movie_details, f, indent=4)
        logger.info(f"Movie Details Results written to {output_file_name}")
        logger.info("Done!")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
