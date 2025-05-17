import yaml
import json
import os


with open("providers.yaml", "r") as f:
    model_list = yaml.safe_load(f)

res_model_list = []

for model in model_list:
    api_key_env = model["litellm_params"].pop("api_key_env")
    # model["litellm_params"]["api_key"] = os.getenv(api_key_env)

    # print(os.getenv(api_key_env))
    # print(type(os.getenv(api_key_env)))
    api_keys_list = json.loads(os.getenv(api_key_env))
    if '[' not in os.getenv(api_key_env):
        continue
    for api_key in api_keys_list:
        model_copy = model.copy()
        model_copy["litellm_params"]["api_key"] = api_key
        res_model_list.append(model_copy)

unique_model_names = set(m["model_name"] for m in model_list)

fallbacks = []
for model in unique_model_names:
    fallbacks.append({
        model: [m["litellm_params"]["model"] for m in res_model_list if m["model_name"] == model]
    })