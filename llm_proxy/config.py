# config.py

# API keys should be set as environment variables, as expected by LiteLLM, e.g.,
# OPENAI_API_KEY="sk-yourkey1,sk-yourkey2"
# ANTHROPIC_API_KEY="sk-ant-yourkey"
# GROQ_API_KEY="gsk_yourkey"
# AZURE_API_KEY="yourkey" (and other AZURE specific env vars like AZURE_API_BASE, AZURE_API_VERSION)

# This configuration helps the server understand which providers and models it *can* attempt to use.
# LiteLLM will ultimately determine if a model is available with the given keys at runtime.

# FR7.2.2: List of used Providers and their names (corresponding to LiteLLM names)
# FR7.2.2: List of models "supported" by each provider (for the /v1/models endpoint)
CONFIGURED_PROVIDERS = {
    "openai": {
        "litellm_provider_name": "openai", # or "azure" if it's an Azure OpenAI deployment
        "models": [
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-3.5-turbo"
        ],
        # For Azure, you would also need to specify api_base, api_version, etc.
        # LiteLLM handles these via environment variables primarily.
        # Example for Azure:
        # "api_base": os.environ.get("AZURE_API_BASE"),
        # "api_version": os.environ.get("AZURE_API_VERSION"),
        # "deployment_id_mapping": { # if model name is different from deployment id
        #    "gpt-4o": "my-gpt-4o-deployment"
        # }
    },
    "anthropic": {
        "litellm_provider_name": "anthropic",
        "models": [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]
    },
    "groq": {
        "litellm_provider_name": "groq",
        "models": [
            "llama3-8b-8192",
            "llama3-70b-8192",
            "mixtral-8x7b-32768",
            "gemma-7b-it"
        ]
    },
    "openrouter": {
        "litellm_provider_name": "openrouter",
        "models": [
            "qwen/qwen3-0.6b-04-28:free",
            "qwen/qwen3-1.7b:free",
            "google/gemini-2.0-flash-exp:free",
            "google/gemma-3-4b-it:free"
        ]
    },
    # Example for a specific Azure OpenAI deployment if keys are set for it
    # "azure_openai_canada": {
    #     "litellm_provider_name": "azure", # LiteLLM uses 'azure' for Azure OpenAI
    #     "models": ["gpt-4-canada", "gpt-35-turbo-canada"], # These are custom names you might use
    #     # LiteLLM expects specific env vars for Azure like AZURE_API_KEY, AZURE_API_BASE, AZURE_API_VERSION
    #     # To map these custom names to actual Azure deployment IDs, you might need to adjust
    #     # how LiteLLM is called, or ensure your env vars are set for specific models if LiteLLM supports that.
    #     # Often, for Azure, the model parameter in litellm.completion is the deployment ID.
    #     # So, "gpt-4-canada" would be your deployment_id for an Azure OpenAI model.
    # }
}

# FR7.2.2: Order of priority of Providers (for FR2.2.3 - choosing provider if model name alone is given)
# This list defines the order in which to check providers if a model name (e.g., "gpt-4o")
# is requested without a specific provider prefix (e.g., "openai/gpt-4o").
# The first provider in this list that supports the model and has available keys will be chosen.
# Keys are the names used in CONFIGURED_PROVIDERS.
PROVIDER_PRIORITY = [
    "openai",
    "anthropic",
    "groq",
    # "azure_openai_canada"
]

# FR7.2.2: Parameters for queue (to be implemented later)
MAX_QUEUE_SIZE = 100
DEFAULT_REQUEST_TIMEOUT_SECONDS = 300 # Default timeout for requests in queue or processing

# FR7.2.2: For each Provider – number of API keys (for managing internal semaphore logic)
# This is for more advanced concurrency control per provider, beyond LiteLLM's default key rotation.
# For now, we rely on LiteLLM's handling of multiple keys in env vars (e.g., OPENAI_API_KEY="k1,k2").
# Example:
# PROVIDER_CONCURRENCY = {
#     "openai": 2, # Max 2 concurrent requests to OpenAI provider using its configured keys
#     "anthropic": 1,
#     "groq": 5
# }
# This feature (semaphore logic) will be implemented in a later stage.

# FR6.2: Structure for /v1/models endpoint
# This function transforms CONFIGURED_PROVIDERS into the desired output format.
def get_available_models_list():
    """
    Generates a list of available models based on CONFIGURED_PROVIDERS
    for the /v1/models endpoint.
    """
    model_map = {} # To group providers by model name
    # First, collect all models and the providers that list them
    for provider_key, provider_config in CONFIGURED_PROVIDERS.items():
        provider_name_for_output = provider_key # Use the key from CONFIGURED_PROVIDERS as the identifier
        for model_name in provider_config.get("models", []):
            # Handle models that might be listed with provider prefix in config (e.g. "openai/gpt-4o")
            # For the output, we want the base model name and a list of providers.
            base_model_name = model_name.split('/')[-1]

            if base_model_name not in model_map:
                model_map[base_model_name] = {"name": base_model_name, "providers": set()}
            model_map[base_model_name]["providers"].add(provider_name_for_output)

    # Also, consider models that might be specified with a provider prefix in the config
    # e.g. if a user explicitly configures "openai/gpt-4o" as a distinct entry.
    # The current logic correctly extracts "gpt-4o" as base_model_name.

    # Convert sets of providers to lists for JSON output
    available_models = []
    for model_info in model_map.values():
        model_info["providers"] = sorted(list(model_info["providers"]))
        available_models.append(model_info)
    
    # Add models that are configured with an explicit provider prefix,
    # ensuring they are also listed as per FR6.2 example like "openai/gpt-3.5-turbo"
    for provider_key, provider_config in CONFIGURED_PROVIDERS.items():
        provider_name_for_output = provider_key
        for model_name in provider_config.get("models", []):
            if '/' in model_name: # e.g., "openai/gpt-3.5-turbo"
                # Check if this specific prefixed entry is already effectively covered
                # by the base model name logic. If not, or if we want to be explicit:
                is_already_listed_explicitly = any(
                    m["name"] == model_name and provider_name_for_output in m["providers"]
                    for m in available_models
                )
                if not is_already_listed_explicitly:
                    # Ensure it's added if it represents a distinct way to call a model
                    # (though typically LiteLLM handles provider from the model string if prefixed)
                    # For FR6.2, if "openai/gpt-3.5-turbo" is in config, it should be listed.
                    # The current model_map logic uses base names. We might need to adjust
                    # if the requirement is to list *exactly* as in config plus the grouped ones.

                    # Let's refine: the output should list unique model *identifiers* that can be used in requests.
                    # If "openai/gpt-4o" is a configured model string, it should be listed.
                    # If "gpt-4o" is also configured under "openai", it's effectively the same for this provider.

                    # The FR6.2 example shows:
                    # {"name": "gpt-4", "providers": ["openai", "azure_openai"]},
                    # {"name": "openai/gpt-3.5-turbo", "providers": ["openai"]},
                    # This implies that "name" can be a base name OR a prefixed name.

                    # Let's stick to the initial model_map logic which groups by base model name,
                    # and then add any explicitly prefixed models from the config if they aren't
                    # already represented for that provider.

                    # Re-thinking FR6.2: "Список моделей, которые Сервер может попытаться использовать"
                    # This means all unique model strings defined in the config.
                    pass # The current logic for model_map should be sufficient if users query by base model name.
                         # If they query by "openai/gpt-4o", our server logic (FR2) will handle that.
                         # The /v1/models endpoint is more about discoverability of what base models exist and where.

    # Sort the final list by model name for consistent output
    return sorted(available_models, key=lambda x: x["name"])

if __name__ == '__main__':
    # For testing the config functions
    print("Configured Providers:", CONFIGURED_PROVIDERS)
    print("\nAvailable Models for /v1/models endpoint:")
    for model_data in get_available_models_list():
        print(model_data)
