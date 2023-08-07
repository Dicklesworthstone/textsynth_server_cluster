#!/bin/bash

echo "This script will install ts_server with the llama2_13B_chat model on Ubuntu."
# Get the user's HOME directory
USER_HOME=$(eval echo ~$USER)

# Path to the current script
SCRIPT_PATH="$(realpath $0)"

# Directory where ts_server will be installed
TS_SERVER_DIR="$USER_HOME/ts_server_free-2023-07-21"
echo "ts_server will be installed in $TS_SERVER_DIR"

# Check if setup_complete file exists
if [ ! -f "$TS_SERVER_DIR/setup_complete" ]; then
  echo "setup_complete file not found. Running setup process..."
  echo "Installing dependencies..."
  sudo apt-get update
  sudo apt-get install -y libmicrohttpd12 libmicrohttpd-dev build-essential cmake git
  echo "Dependencies installed."
  
  echo "Downloading and extracting ts_server..."
  cd "$USER_HOME"
  wget https://bellard.org/ts_server/ts_server_free-2023-07-21.tar.gz
  tar xzf ts_server_free-2023-07-21.tar.gz || { echo "Error extracting ts_server. Exiting."; exit 1; }
  cd "$TS_SERVER_DIR"
  echo "ts_server successfully downloaded and extracted."
  echo "Now downloading llama2_13B_chat model. This may take a while..."
  wget https://huggingface.co/fbellard/ts_server/resolve/main/llama2_13B_chat_q4.bin 
  MODEL_SIZE=$(stat -c %s "$TS_SERVER_DIR/llama2_13B_chat_q4.bin")
  EXPECTED_SIZE="7000000000" # Approximate size in bytes, adjust as needed
  if [ "$MODEL_SIZE" -lt "$EXPECTED_SIZE" ]; then
    echo "Error: Model file is smaller than expected. Download may have failed."
    exit 1
  fi
  echo "Model download complete."

  echo "Downloading and compiling libjpeg-turbo. This may take a while..."
  wget https://github.com/libjpeg-turbo/libjpeg-turbo/archive/refs/tags/2.1.5.1.tar.gz
  tar xzf 2.1.5.1.tar.gz
  cd libjpeg-turbo-2.1.5.1/
  mkdir build
  cd build
  cmake -G"Unix Makefiles" CC='zig cc' ../
  make
  sudo make install
  echo "libjpeg-turbo successfully installed."

  echo "Updating ts_server.cfg..."
  cd "$TS_SERVER_DIR"
  sed -i 's/{ name: "gpt2_117M",  filename: "gpt2_117M.bin" },/{ name: "llama2_13B_chat",  filename: "llama2_13B_chat_q4.bin" },/' ts_server.cfg
  sed -i 's/n_threads: 1,/n_threads: 4,/' ts_server.cfg
  sed -i 's/  local_port: 8080,/  local_port: 8088,/' ts_server.cfg

  echo "Now copying this script to the ts_server directory and making it executable... to run ts_server, simply run this script again."
  cp "$SCRIPT_PATH" .
  chmod +x "$(basename $SCRIPT_PATH)"

  echo "Now creating the `setup_complete` file so this script knows to skip the setup process next time."
  touch setup_complete
  echo "Setup complete!"
fi

echo "Now running ts_server with llama2_13B_chat model on port 8088..."
echo "The ts_server log will be saved to $TS_SERVER_DIR/ts_server.log"
nohup env LD_LIBRARY_PATH=/opt/libjpeg-turbo/lib64/ "$TS_SERVER_DIR/ts_server" "$TS_SERVER_DIR/ts_server.cfg" > "$TS_SERVER_DIR/ts_server.log" 2>&1 &
