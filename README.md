# TextSynth Server Cluster for Parallel Inference

## Overview

This project provides a way to utilize a collection of Ubuntu servers to create a low-cost cluster for parallel inference using Fabrice Bellard's [ts_server](https://bellard.org/ts_server/). 

Even if the servers do not have a GPU, they can be quickly deployed with ts_server using Ansible to automatically download and utilize a specified language model like the llama2 13b chat LLM.

By distributing inference requests across multiple servers, you can efficiently process large numbers of requests in parallel. This makes it possible to leverage existing hardware resources for scalable, concurrent processing without the need for specialized GPU hardware.

## How It Works

1. **Deploying ts_server**: Use Ansible to deploy ts_server to all available Ubuntu servers in your cluster.
2. **Model Selection**: Configure the specific language model to be used (e.g., llama2 13b chat LLM).
3. **Parallel Inference**: Submit parallel inference requests asynchronously to the cluster.
4. **Results Gathering**: Gather the results together for further processing or analysis.

## Getting Started

### Prerequisites

- A collection of Ubuntu servers (tested on Ubuntu 22.04).
- Ansible for deployment.
- Python 3.x.
- To install Ansible:
```bash
sudo apt update
sudo apt install ansible -y
```
- Prepare an ansible inventory (e.g., `my_ansible_inventory_for_ts_server_cluster.ini`) for your remote machines like this:
```
[ts_servers]
server1 ansible_host=192.168.1.10 ansible_user=ubuntu
server2 ansible_host=192.168.1.11 ansible_user=ubuntu
server3 ansible_host=192.168.1.12 ansible_user=ubuntu

[all:vars]
ansible_ssh_private_key_file=/path/to/your/private/key.pem
```

### Installation

1. Clone the repository.
2. Configure your Ansible inventory file with the details of your Ubuntu servers.
3. Customize `run_ts_server_with_llama2_13b_chat_on_ubuntu.sh` as needed to change the LLM model you want to use or the port that ts_server will listen on.
4. Run the Ansible playbook to deploy ts_server and the specified language model to each server.
5. Adjust the Python script's parameters as needed for your environment, such as the number of concurrent requests and timeout settings.

### Usage

- Use the provided Python script to send inference requests to the cluster.
- View the results in the specified output files.
Certainly! Here's an expanded description that covers both the use cases shown in the code:

### Example Use Cases: Movie Synopsis Extraction and Movie Details Extraction

Included in this project are two specific examples related to movies: extracting movie synopses and extracting detailed movie information. Both examples demonstrate the power of parallel processing using the created cluster of servers.

#### 1. Movie Synopsis Extraction

The script first generates prompts to provide short synopses for a list of movies. The prompts are designed to keep the response concise and focused on the main storyline. Example:

```plaintext
Please provide a short synopsis of the plot of the movie "Forrest Gump." Keep it concise and focused on the main storyline.

Response: The synopsis of "Forrest Gump" is:
```

These prompts are then sent to the ts_server cluster, which processes them in parallel. The resulting synopses are gathered and saved to a JSON file. This demonstrates the ability to efficiently process a large number of similar requests in parallel.

#### 2. Movie Details Extraction

The second use case extracts detailed information about movies in the form of a JSON object. The details include the movie's title, release year, director, genre, and main actors. Example prompt:

```plaintext
Random Seed: 42

Please provide details of the movie "The Godfather" in the form of a JSON object with the following keys:
- "title": Title of the movie
- "release_year": Year the movie was released
- "director": Name of the director
- "genre": Genre of the movie
- "main_actors": List of main actors

Response: The details of "The Godfather" are:
```

The script takes care to validate and correct any JSON formatting issues in the model's response. If the JSON is not valid, the script retries with a different random seed, ensuring robustness in handling potential inconsistencies in the responses.

These two use cases showcase different aspects of the cluster's functionality. The synopsis extraction highlights the efficiency of parallel processing, while the details extraction demonstrates more complex interaction with the model, including data validation and error handling. Combined, they provide a powerful example of how the cluster can be leveraged for diverse and complex tasks.

## TS Server Installation Script

The included installation script automates the process of setting up the ts_server with the llama2_13B_chat model on an Ubuntu server. Here's a summary of what the script does:

1. **Checks for Previous Installation**: The script first checks if ts_server has been previously installed by looking for a `setup_complete` file. If found, it skips the installation process.

2. **Installs Dependencies**: It installs necessary dependencies such as libmicrohttpd12, libmicrohttpd-dev, build-essential, cmake, and git.

3. **Downloads and Extracts ts_server**: Downloads the ts_server archive and extracts it to a specified directory.

4. **Downloads llama2_13B_chat Model**: Downloads the specific llama2_13B_chat model and verifies the download by checking the file size.

5. **Installs libjpeg-turbo**: Downloads, compiles, and installs libjpeg-turbo, a JPEG image codec that uses SIMD instructions.

6. **Updates ts_server Configuration**: Modifies the `ts_server.cfg` file to set up the desired model, number of threads, and port number.

7. **Sets Up Script for Future Use**: Copies the script to the ts_server directory and makes it executable, so it can be used to run ts_server in the future. 

8. **Creates `setup_complete` File**: Creates a `setup_complete` file to indicate that the setup process has been completed, so it won't run again the next time the script is executed.

9. **Runs ts_server**: Finally, the script runs ts_server with the llama2_13B_chat model on port 8088, and logs the output to a specified log file.

To run the script, simply execute it from the command line. If ts_server and the model are already installed, the script will start ts_server; otherwise, it will perform the full installation process.

This script provides a streamlined way to set up ts_server with a specific model, making it easy to deploy across multiple servers in the cluster.


## Ansible Playbook for Deploying and Running ts_server

This Ansible playbook allows you to quickly deploy and run the ts_server with the llama2_13b_chat model on a cluster of Ubuntu servers. Here's a step-by-step breakdown of the playbook tasks:

1. **Copy Bash Script to Remote Host**: Copies the provided bash script (`run_ts_server_with_llama2_13b_chat_on_ubuntu.sh`) to the remote host's home directory, setting the appropriate permissions.

2. **Execute the Bash Script**: Executes the copied bash script on the remote host. It allows 30 minutes for completion, which accounts for potential slow network connections when downloading the large model file (~7GB). The task polls every 30 seconds to check for completion.

3. **Check if ts_server is Running**: Uses the `pgrep` command to determine if ts_server is running on the remote host.

4. **Check if ts_server is Listening on Port 8088**: Checks if ts_server is actively listening on port 8088 using the `lsof` command.

5. **Show Log if ts_server is Not Running or Not Listening**: If ts_server is not running or not listening on the designated port, this task retrieves the last 10 lines of the ts_server log.

6. **Print Log if ts_server is Not Running or Not Listening**: Prints the retrieved log if ts_server is not running or not listening, aiding in troubleshooting.

7. **Clean Up Temporary Script File**: Removes the temporary script file used to deploy and run ts_server from the remote host's home directory.

This playbook automates the deployment and execution of ts_server across multiple remote machines, ensuring consistent setup and easing the process of managing a cluster. By using this playbook, you can leverage existing Ubuntu servers to create a low-cost, parallel inference cluster for llama2_13b_chat or similar models.

To execute the playbook, run the following command:

```bash
ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i my_ansible_inventory_for_ts_server_cluster.ini all ansible_playbook_to_setup_ts_server_with_llama2_13b_chat.yml -f 50
```

You can see if the remote machines are listening on the correcto port like this:

```bash
 ANSIBLE_HOST_KEY_CHECKING=False ansible -i my_ansible_inventory_for_ts_server_cluster.ini all -m shell -a "sudo lsof -i -P -n | grep ts_server" -f 50
```

And you can check the log files on the remote machines easily like this:

```bash
ANSIBLE_HOST_KEY_CHECKING=False ansible -i my_ansible_inventory_for_ts_server_cluster.ini all -m shell -a "tail -n 10 /home/ubuntu/ts_server_free-2023-07-21/ts_server.log" -f 50
```

## Python Script Showing Example Usage

### Overview:
Once you have deployed everything to your ansible inventory and verified that ts_server is running on the right port and awaiting requests, you can run the example python script. This script is designed to efficiently send parallel requests to a cluster of `ts_server` nodes for the purpose of chatbot-like interactions. The primary use case demonstrated here is to obtain movie synopses and detailed descriptions of a list of movies using the `llama2_13B_chat` model deployed across the cluster.

### Python Script Setup:
These commands create a virtual environment, activate it, upgrade `pip`, and then install the required dependencies from the `requirements.txt` file:

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

### Details:

#### 1. **Imports and Configurations**:
The script starts by importing necessary libraries like `httpx` (for asynchronous HTTP requests), `asyncio`, and others. It also sets up some constants like `CONCURRENT_REQUESTS`, `RETRY_COUNT`, and timeouts.

#### 2. **Extracting IPs from Ansible Inventory** (`extract_ips_from_ansible_inventory`):
This function reads an Ansible inventory file (either YAML or INI format) and extracts IP addresses of all the hosts, saving them in a text file. This list of IP addresses represents the nodes in the `ts_server` cluster.

#### 3. **IP Validation and Availability Check** (`validate_ip`, `check_ip_availability`):
- `validate_ip`: Validates if a given string is a proper IP address.
- `check_ip_availability`: Asynchronously checks if the `ts_server` on a given IP is responsive by sending a GET request to its root path.

#### 4. **Single Server Testing** (`test_single_server`):
This function sends a predefined prompt to a given `ts_server` IP to test its responsiveness and measures the time taken for the completion of the inference.

#### 5. **Testing All Servers** (`test_ts_servers`):
This function reads the list of IP addresses from the text file, validates them, and tests each one using the aforementioned single server test function. It then collates the results.

#### 6. **Sending Requests to Servers** (`send_request`):
This asynchronous function sends a chat prompt to a given `ts_server` IP. It handles HTTP errors and read timeouts and will retry sending the request if it fails, up to a predefined `RETRY_COUNT`.

#### 7. **Round Robin Request Processing** (`round_robin_request`):
The script employs a round-robin strategy to distribute prompts to the servers. Live IPs are first determined by checking their availability. Then, using semaphores to limit concurrent requests, the script sends prompts to the servers in a cyclic manner. This ensures an even distribution of workload across the cluster.

#### 8. **Generating Movie Prompts** (`generate_movie_synopsis_prompt`, `generate_movie_synopsis_prompts`, `generate_movie_details_prompt`, `generate_movie_details_prompts`):
These functions help generate structured prompts for the chat model:
- For requesting a movie's synopsis.
- For requesting detailed movie info in a JSON format.

The random seed is added to ensure variability in responses, making it easier to obtain different details in case of retries.

#### 9. **Processing Model Responses** (`validate_and_correct_json`, `extract_movie_title_from_prompt`, `get_movie_details`, `get_all_movie_details`):
- The script tries to correct common issues in the model's JSON response, ensuring it's valid.
- For movie details, the script can send multiple prompts (with retries) until it receives a valid JSON response from the model.

#### 10. **Main Execution**:
In the `if __name__ == "__main__":` block:
- IP addresses are extracted from the Ansible inventory.
- The `ts_servers` are tested for responsiveness.
- Movie synopsis prompts are generated and sent to the servers.
- Detailed movie descriptions are requested in JSON format.

All results are saved to JSON files.

### Design Decisions:

1. **Asynchronous Operations**: The script uses Python's `asyncio` to send parallel requests to the `ts_server` nodes, maximizing the throughput and reducing the total time taken for all requests.
  
2. **Round Robin Distribution**: This method ensures an even distribution of requests across the cluster, preventing any single node from being a bottleneck.

3. **Retries**: Given the potential for network issues or server hiccups, the script has a retry mechanism, ensuring that transient issues don't result in failed prompts.

4. **Dynamic Prompt Generation**: By generating prompts dynamically, especially with random seeds, the script can elicit varied and comprehensive responses from the model.

5. **Response Validation and Correction**: The script tries to sanitize and validate the model's response, ensuring that the gathered data is in the correct format.

---

This script provides a robust method for leveraging a cluster of `ts_server` nodes to get detailed and accurate information from the `llama2_13B_chat` model. By handling IP validation, server responsiveness checks, structured prompt generation, and response validation, it ensures reliable and consistent results.

