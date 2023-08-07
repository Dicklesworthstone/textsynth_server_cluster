#!/bin/bash

# Path to the current script
SCRIPT_PATH="$(realpath $0)"

# Check if setup_complete file exists
if [ ! -f ~/ts_server_free-2023-07-21/setup_complete ]; then
  # Install libmicrohttpd12 and other dependencies
  sudo apt-get update
  sudo apt-get install -y libmicrohttpd12 libmicrohttpd-dev build-essential cmake git

  # Download and extract ts_server
  cd ~
  wget https://bellard.org/ts_server/ts_server_free-2023-07-21.tar.gz
  tar xzf ts_server_free-2023-07-21.tar.gz
  cd ts_server_free-2023-07-21
  wget https://huggingface.co/fbellard/ts_server/resolve/main/llama2_13B_chat_q4.bin 

  # Download and compile libjpeg-turbo
  wget https://github.com/libjpeg-turbo/libjpeg-turbo/archive/refs/tags/2.1.5.1.tar.gz
  tar xzf 2.1.5.1.tar.gz
  cd libjpeg-turbo-2.1.5.1/
  mkdir build
  cd build
  cmake -G"Unix Makefiles" CC='zig cc' ../
  make
  sudo make install

  # Update ts_server.cfg
  cd ~/ts_server_free-2023-07-21
  sed -i 's/{ name: "gpt2_117M",  filename: "gpt2_117M.bin" },/{ name: "llama2_13B_chat",  filename: "llama2_13B_chat_q4.bin" },/' ts_server.cfg
  sed -i 's/n_threads: 1,/n_threads: 4,/' ts_server.cfg
  sed -i 's/  local_port: 8080,/  local_port: 8088,/' ts_server.cfg

  # Copy this script to the directory and make it executable
  cp "$SCRIPT_PATH" .
  chmod +x "$(basename $SCRIPT_PATH)"

  # Create setup_complete file
  touch setup_complete
fi

# Run ts_server with the appropriate library path
nohup env LD_LIBRARY_PATH=/opt/libjpeg-turbo/lib64/ /home/ubuntu/ts_server_free-2023-07-21/ts_server /home/ubuntu/ts_server_free-2023-07-21/ts_server.cfg > /home/ubuntu/ts_server_free-2023-07-21/ts_server.log 2>&1 &
