# LLM throughput benchmark

## The benchmark

You crave for perfect code suggestions, but you don't know whether it fits your needs in terms of latency?

We ran our tests on the following hardware:

- [NVIDIA GeForce RTX 3060](https://www.nvidia.com/fr-fr/geforce/graphics-cards/30-series/rtx-3060-3060ti/) (mobile)*
- [NVIDIA GeForce RTX 3070](https://www.nvidia.com/fr-fr/geforce/graphics-cards/30-series/rtx-3070-3070ti/) ([Scaleway GPU-3070-S](https://www.scaleway.com/en/pricing/?tags=compute))
- [NVIDIA A10](https://www.nvidia.com/en-us/data-center/products/a10-gpu/) ([Lambda Cloud gpu_1x_a10](https://lambdalabs.com/service/gpu-cloud#pricing))
- [NVIDIA A10G](https://www.nvidia.com/en-us/data-center/products/a10-gpu/) ([AWS g5.xlarge](https://aws.amazon.com/ec2/instance-types/g5/))
- [NVIDIA L4](https://www.nvidia.com/en-us/data-center/l4/) ([Scaleway L4-1-24G](https://www.scaleway.com/en/pricing/?tags=compute))

*The laptop hardware setup includes an [Intel(R) Core(TM) i7-12700H](https://ark.intel.com/content/www/us/en/ark/products/132228/intel-core-i7-12700h-processor-24m-cache-up-to-4-70-ghz.html) for the CPU*

with the following LLMs (cf. [Ollama hub](https://ollama.com/library)):
- Deepseek Coder 6.7b - instruct ([Ollama](https://ollama.com/library/deepseek-coder), [Hugging Face](https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-instruct))
- OpenCodeInterpreter 6.7b ([Ollama](https://ollama.com/pxlksr/opencodeinterpreter-ds), [Hugging Face](https://huggingface.co/m-a-p/OpenCodeInterpreter-DS-6.7B), [paper](https://arxiv.org/abs/2402.14658))
- Dolphin Mistral 7b ([Ollama](https://ollama.com/library/dolphin-mistral), [Hugging Face](https://huggingface.co/cognitivecomputations/dolphin-2.6-mistral-7b-dpo-laser), [paper](https://arxiv.org/abs/2310.06825))
- Coming soon: StarChat v2 ([Hugging Face](https://huggingface.co/HuggingFaceH4/starchat2-15b-v0.1), [paper](https://arxiv.org/abs/2402.19173))

and the following quantization formats: q3_K_M, q4_K_M, q5_K_M.

This [benchmark](./benchmark_result.csv) was performed over 5 iterations on 4 different sequences, including on a **laptop** to better reflect performances that can be expected by common users.

## Run it on your hardware

### Local setup

Quite simply, start the docker:
```
docker compose up -d --wait
```
Pull the model you want
```
docker compose exec -T ollama ollama pull MODEL
```

And run the evaluation
```
docker compose exec -T evaluator python evaluate.py MODEL
```

### Remote instance

Start the evaluator only
```
docker compose up -d evaluator --wait
```
And run the evaluation by targeting your remote instance:
```
docker compose exec -T evaluator python evaluate.py MODEL --endpoint http://HOST:PORT
```

*All script arguments can be checked using `python scripts/ollama/evaluate_perf.py --help`*

### Others

Here are the results for other LLMs that have have only been evaluated on the laptop GPU:

| Model                                                        | Ingestion mean (std)   | Generation mean (std) |
| ------------------------------------------------------------ | ---------------------- | --------------------- |
| [tinyllama:1.1b-chat-v1-q4_0](https://ollama.com/library/tinyllama:1.1b-chat-v1-q4_0) | 2014.63 tok/s (±12.62) | 227.13 tok/s (±2.26)  |
| [dolphin-phi:2.7b-v2.6-q4_0](https://ollama.com/library/dolphin-phi:2.7b-v2.6-q4_0) | 684.07 tok/s (±3.85)   | 122.25 toks/s (±0.87) |
| [dolphin-mistral:7b-v2.6](https://ollama.com/library/dolphin-mistral:7b-v2.6) | 291.94 tok/s (±0.4)    | 60.56 tok/s (±0.15)   |
