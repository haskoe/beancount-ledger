#!/bin/bash

llama-server \
  -m ~/models/Qwen3VL-8B-Instruct-Q8_0.gguf \
  --mmproj ~/models/mmproj-Qwen3VL-8B-Instruct-F16.gguf \
  --ctx-size 32768 \
  --gpu-layers 99 \
  --host 0.0.0.0 --port 8080