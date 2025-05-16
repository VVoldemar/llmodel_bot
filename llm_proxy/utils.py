import os
import litellm
from flask import abort

from load_data import model_list, fallbacks, unique_model_names

router = litellm.Router(
    model_list=model_list,
    fallbacks=fallbacks,
    num_retries=3,
    timeout=10
)


def check_api_key(api_key: str) -> bool:
    """
    Check if the API key is valid.
    """
    if not api_key or api_key != os.getenv("ACCESS_API_KEY"):
        print(api_key, os.getenv("ACCESS_API_KEY"), type(api_key), type(os.getenv("ACCESS_API_KEY")))
        abort(401, "Invalid API key")
    

def valid_model_request(request: dict) -> bool:
    """
    Check if the request is valid.
    """
    api_key = request.get("api_key")
    check_api_key(api_key)

    if "model" not in request or "messages" not in request:
        abort(400, "Missing model or messages in request")
    if request["model"] not in unique_model_names:
        abort(400, "Invalid model name")
    if not isinstance(request["messages"], list):
        abort(400, "Messages should be a list")
    if len(request["messages"]) == 0:
        abort(400, "Messages list cannot be empty")
    for message in request["messages"]:
        if "role" not in message or message["role"] not in ["system", "user", "assistant"] or "content" not in message:
            abort(400, "Each message must contain a role (one of ['system', 'user', 'assistant']) and content")
    return True


# def generate(model: str="github/ministral-3B", messages: list=[]):
#     response = router.completion(
#         model=model, 
#         messages=messages,
#         stream=True
#     )
#     for chunk in response:
#         delta = chunk.choices[0].delta
#         content = delta.content
#         if content:
#             yield content


def generate(model: str="github/ministral-3B", messages: list=[]):
    """
    Generate a response from the model.
    """
    response = router.completion(
        model=model, 
        messages=messages,
        stream=True
    )
    first_chunk = True
    reasoning = False

    if model == "phi-4-reasoning":
        last_chunk = False
        reasoning = True
        yield "<reasoning>\n"
        for chunk in response:

            delta = chunk.choices[0].delta
            content = delta.content

            if content:
                if reasoning and "───" in content:
                    reasoning = False
                    yield "</reasoning>\n\n"
                yield content
            
    else:
        for chunk in response:

            delta = chunk.choices[0].delta
            if first_chunk:
                first_chunk = False
                if "reasoning" in delta:
                    reasoning = True
                    yield "<reasoning>"

            if reasoning:
                if delta.reasoning is not None:
                    yield delta.reasoning
                    # continue
                else:
                    yield "</reasoning>"
                    reasoning = False

            content = delta.content
            if content:
                yield content