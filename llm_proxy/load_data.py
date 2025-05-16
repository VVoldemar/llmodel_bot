import yaml
import os


with open("providers.yaml", "r") as f:
    model_list = yaml.safe_load(f)

for model in model_list:
    api_key_env = model["litellm_params"].pop("api_key_env")
    model["litellm_params"]["api_key"] = os.getenv(api_key_env)

unique_model_names = set(m["model_name"] for m in model_list)

fallbacks = []
for model in unique_model_names:
    fallbacks.append({
        model: [m["litellm_params"]["model"] for m in model_list if m["model_name"] == model]
    })