# TextSynth Server Cluster for Parallel Inference

## Overview

This project provides a way to utilize a collection of Ubuntu servers to create a low-cost cluster for parallel inference using Fabrice Bellard's [ts_server](https://bellard.org/ts_server/). 

Even if the servers do not have a GPU, they can be quickly deployed with ts_server using Ansible to automatically download and utilize a specified language model like the llama2 13b chat LLM.

By distributing inference requests across multiple servers, you can efficiently process large numbers of requests in parallel. 

This makes it possible to leverage existing hardware resources for scalable, concurrent processing without the need for specialized GPU hardware.

## How It Works

1. **Deploying ts_server**: Use Ansible to deploy ts_server to all available Ubuntu servers in your cluster.
2. **Model Selection**: Configure the specific language model to be used (e.g., llama2 13b chat LLM).
3. **Parallel Inference**: Submit parallel inference requests asynchronously to the cluster.
4. **Results Gathering**: Gather the results together for further processing or analysis.

## Getting Started

### Prerequisites

- A collection of Ubuntu servers.
- Ansible for deployment.
- Python 3.x.

### Installation

1. Clone the repository.
2. Configure your Ansible inventory file with the details of your Ubuntu servers.
3. Run the Ansible playbook to deploy ts_server and the specified language model to each server.
4. Adjust the Python script's parameters as needed for your environment, such as the number of concurrent requests and timeout settings.

### Usage

- Use the provided Python script to send inference requests to the cluster.
- View the results in the specified output files.

## Example Use Case: Movie Details Extraction

Included in this project is a specific example of extracting movie details and synopses. The script generates prompts for movie details and sends them to the cluster for parallel processing. The results are then gathered and saved.

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
ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i your_inventory_file.ini ansible_playbook_to_setup_ts_server_with_llama2_13b_chat.yml -f 50
```

You can see if the remote machines are listening on the correcto port like this:

```bash
 ANSIBLE_HOST_KEY_CHECKING=False ansible -i your_inventory_file.ini -m shell -a "sudo lsof -i -P -n | grep ts_server" -f 50
```

And you can check the log files on the remote machines easily like this:

```bash
ANSIBLE_HOST_KEY_CHECKING=False ansible -i your_inventory_file.ini -m shell -a "tail -n 10 /home/ubuntu/ts_server_free-2023-07-21/ts_server.log" -f 50
```



