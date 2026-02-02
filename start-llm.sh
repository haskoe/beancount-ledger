#!/bin/bash

llama-server \
  -m ~/models/Qwen3VL-8B-Instruct-Q8_0.gguf \
  --mmproj ~/models/mmproj-Qwen3VL-8B-Instruct-F16.gguf \
  --ctx-size 8192 \
  --batch-size 256 \
  --ubatch-size 256 \
  --gpu-layers 99 \
#  -fa on
# -ctk q4_0 -ctv q4_0
  --host 0.0.0.0 --port 8080 &

llama-server \
  -m ~/models/Qwen3VL-8B-Instruct-Q8_0 gemma-2-2b-it-q8_0.gguf \
  --port 8081 \
  --ctx-size 4096 \
  --gpu-layers 99 \
  --no-mmap \
  -fa on
  --host 0.0.0.0
  # gemma-2-2b-it-q8_0.gguf  

  llama-server --jinja --min-p 0.01 --temp 0.15 --batch-size 2048 --ctx-size 230000 --cont-batching --cache-type-k q8_0 --cache-type-v q4_0 --flash-attn on --fit on --fit-ctx 230000 --kv-unified --model unsloth.Devstral-Small-2-24B-Instruct-2512-UD-Q4_K_XL.gguf --parallel 1 --threads 12 --threads-batch 24 --ubatch-size 2048

  docker run --rm -v $(pwd)/config:/etc/teleport public.ecr.aws/gravitational/teleport:14 configure --cluster-name=teleport.haskoe.dk --public-addr=teleport.haskoe.dk:443 --cert-file=/etc/teleport/fullchain.pem --key-file=/etc/teleport/privkey.pem > ./config/teleport.yaml
docker run --rm -v $(pwd)/config:/etc/teleport public.ecr.aws/gravitational/teleport:14 teleport configure --cluster-name=teleport.haskoe.dk --public-addr=teleport.haskoe.dk:443 --cert-file=/etc/teleport/fullchain.pem --key-file=/etc/teleport/privkey.pem > ./config/teleport.yaml