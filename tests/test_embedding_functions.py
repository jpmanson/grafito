import types

import pytest

from grafito.embedding_functions import (
    HuggingFaceEmbeddingFunction,
    OpenAIEmbeddingFunction,
    CohereEmbeddingFunction,
    OllamaEmbeddingFunction,
    AmazonBedrockEmbeddingFunction,
    JinaEmbeddingFunction,
    VoyageAIEmbeddingFunction,
    MistralEmbeddingFunction,
    GoogleGenAIEmbeddingFunction,
    TensorFlowHubEmbeddingFunction,
    TogetherAIEmbeddingFunction,
)


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class DummyClient:
    last_headers = None
    last_payload = None
    last_url = None
    responses = []

    def __init__(self):
        self.headers = {}
        DummyClient.last_headers = self.headers

    def post(self, url, json):
        DummyClient.last_payload = json
        DummyClient.last_url = url
        if DummyClient.responses:
            return DummyResponse(DummyClient.responses.pop(0))
        return DummyResponse([[0.1, 0.2, 0.3]])


def _install_dummy_httpx(monkeypatch):
    dummy_httpx = types.SimpleNamespace(Client=DummyClient)
    monkeypatch.setitem(__import__("sys").modules, "httpx", dummy_httpx)


def test_hf_embedding_explicit_key_overrides_env(monkeypatch):
    _install_dummy_httpx(monkeypatch)
    monkeypatch.setenv("HF_TOKEN", "env-token")
    DummyClient.responses = [[[0.1, 0.2, 0.3]]]

    embedder = HuggingFaceEmbeddingFunction(api_key="explicit-token")
    embedder(["hello"])

    assert DummyClient.last_headers["Authorization"] == "Bearer explicit-token"


def test_hf_embedding_env_fallback(monkeypatch):
    _install_dummy_httpx(monkeypatch)
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.setenv("HUGGINGFACE_HUB_TOKEN", "hub-token")
    DummyClient.responses = [[[0.1, 0.2, 0.3]]]

    embedder = HuggingFaceEmbeddingFunction()
    embedder(["hello"])

    assert DummyClient.last_headers["Authorization"] == "Bearer hub-token"


def test_hf_embedding_requires_key(monkeypatch):
    _install_dummy_httpx(monkeypatch)
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("HUGGINGFACE_HUB_TOKEN", raising=False)
    monkeypatch.delenv("HUGGINGFACEHUB_API_TOKEN", raising=False)
    monkeypatch.delenv("HUGGINGFACE_API_KEY", raising=False)

    with pytest.raises(ValueError, match="Hugging Face API token not provided"):
        HuggingFaceEmbeddingFunction()


def test_hf_embedding_build_from_config(monkeypatch):
    _install_dummy_httpx(monkeypatch)
    monkeypatch.setenv("MY_HF_TOKEN", "config-token")
    DummyClient.responses = [[[0.1, 0.2, 0.3]]]

    embedder = HuggingFaceEmbeddingFunction.build_from_config(
        {"model_name": "test-model", "api_key_env_var": "MY_HF_TOKEN"}
    )
    embedder(["hello"])

    assert DummyClient.last_headers["Authorization"] == "Bearer config-token"


def test_openai_embedding_explicit_key_overrides_env(monkeypatch):
    _install_dummy_httpx(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "env-openai")
    DummyClient.responses = [{"data": [{"embedding": [0.2, 0.3]}]}]

    embedder = OpenAIEmbeddingFunction(api_key="explicit-openai")
    embedder(["hello"])

    assert DummyClient.last_headers["Authorization"] == "Bearer explicit-openai"


def test_openai_embedding_env_fallback(monkeypatch):
    _install_dummy_httpx(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "env-openai")
    DummyClient.responses = [{"data": [{"embedding": [0.2, 0.3]}]}]

    embedder = OpenAIEmbeddingFunction()
    embedder(["hello"])

    assert DummyClient.last_headers["Authorization"] == "Bearer env-openai"


def test_openai_embedding_requires_key(monkeypatch):
    _install_dummy_httpx(monkeypatch)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OpenAI API key not provided"):
        OpenAIEmbeddingFunction()


def test_openai_embedding_build_from_config(monkeypatch):
    _install_dummy_httpx(monkeypatch)
    monkeypatch.setenv("OPENAI_TOKEN", "config-openai")
    DummyClient.responses = [{"data": [{"embedding": [0.2, 0.3]}]}]

    embedder = OpenAIEmbeddingFunction.build_from_config(
        {"model": "test-model", "api_key_env_var": "OPENAI_TOKEN"}
    )
    embedder(["hello"])

    assert DummyClient.last_headers["Authorization"] == "Bearer config-openai"


def test_cohere_embedding_explicit_key_overrides_env(monkeypatch):
    _install_dummy_httpx(monkeypatch)
    monkeypatch.setenv("COHERE_API_KEY", "env-cohere")
    DummyClient.responses = [{"embeddings": [[0.5, 0.6]]}]

    embedder = CohereEmbeddingFunction(api_key="explicit-cohere")
    embedder(["hello"])

    assert DummyClient.last_headers["Authorization"] == "Bearer explicit-cohere"


def test_cohere_embedding_env_fallback(monkeypatch):
    _install_dummy_httpx(monkeypatch)
    monkeypatch.setenv("COHERE_API_KEY", "env-cohere")
    DummyClient.responses = [{"embeddings": [[0.5, 0.6]]}]

    embedder = CohereEmbeddingFunction()
    embedder(["hello"])

    assert DummyClient.last_headers["Authorization"] == "Bearer env-cohere"


def test_cohere_embedding_requires_key(monkeypatch):
    _install_dummy_httpx(monkeypatch)
    monkeypatch.delenv("COHERE_API_KEY", raising=False)

    with pytest.raises(ValueError, match="Cohere API key not provided"):
        CohereEmbeddingFunction()


def test_cohere_embedding_build_from_config(monkeypatch):
    _install_dummy_httpx(monkeypatch)
    monkeypatch.setenv("COHERE_TOKEN", "config-cohere")
    DummyClient.responses = [{"embeddings": [[0.5, 0.6]]}]

    embedder = CohereEmbeddingFunction.build_from_config(
        {"model": "test-model", "api_key_env_var": "COHERE_TOKEN"}
    )
    embedder(["hello"])

    assert DummyClient.last_headers["Authorization"] == "Bearer config-cohere"


def test_ollama_embedding_uses_env_host(monkeypatch):
    _install_dummy_httpx(monkeypatch)
    monkeypatch.setenv("OLLAMA_HOST", "http://ollama.local:11434")
    DummyClient.responses = [{"embedding": [0.8, 0.9]}]

    embedder = OllamaEmbeddingFunction(model="nomic-embed-text")
    embedder(["hello"])

    assert DummyClient.last_url == "http://ollama.local:11434/api/embeddings"


def test_amazon_bedrock_embedding_uses_session_args(monkeypatch):
    class DummyBody:
        def read(self):
            return b'{"embedding": [0.1, 0.2]}'

    class DummyBedrockClient:
        def invoke_model(self, **kwargs):
            return {"body": DummyBody()}

    class DummySession:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.region_name = kwargs.get("region_name")
            self.profile_name = kwargs.get("profile_name")

        def client(self, service_name, **kwargs):
            assert service_name == "bedrock-runtime"
            return DummyBedrockClient()

    dummy_boto3 = types.SimpleNamespace(Session=DummySession)
    monkeypatch.setitem(__import__("sys").modules, "boto3", dummy_boto3)

    embedder = AmazonBedrockEmbeddingFunction(
        model_name="amazon.titan-embed-text-v1",
        region_name="us-east-1",
        profile_name="test-profile",
    )
    embedder(["hello"])

    assert embedder.get_config()["session_args"] == {
        "region_name": "us-east-1",
        "profile_name": "test-profile",
    }


def test_amazon_bedrock_build_from_config(monkeypatch):
    class DummyBody:
        def read(self):
            return b'{"embedding": [0.2, 0.3]}'

    class DummyBedrockClient:
        def invoke_model(self, **kwargs):
            return {"body": DummyBody()}

    class DummySession:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.region_name = kwargs.get("region_name")
            self.profile_name = kwargs.get("profile_name")

        def client(self, service_name, **kwargs):
            assert service_name == "bedrock-runtime"
            return DummyBedrockClient()

    dummy_boto3 = types.SimpleNamespace(Session=DummySession)
    monkeypatch.setitem(__import__("sys").modules, "boto3", dummy_boto3)

    embedder = AmazonBedrockEmbeddingFunction.build_from_config(
        {
            "model_name": "amazon.titan-embed-text-v1",
            "session_args": {"region_name": "us-west-2"},
        }
    )
    embedder(["hello"])

    assert embedder.get_config()["session_args"] == {"region_name": "us-west-2"}


def test_jina_embedding_explicit_key_overrides_env(monkeypatch):
    _install_dummy_httpx(monkeypatch)
    monkeypatch.setenv("JINA_API_KEY", "env-jina")
    DummyClient.responses = [{"data": [{"index": 0, "embedding": [0.4, 0.5]}]}]

    embedder = JinaEmbeddingFunction(api_key="explicit-jina")
    embedder(["hello"])

    assert DummyClient.last_headers["Authorization"] == "Bearer explicit-jina"


def test_jina_embedding_env_fallback(monkeypatch):
    _install_dummy_httpx(monkeypatch)
    monkeypatch.setenv("JINA_API_KEY", "env-jina")
    DummyClient.responses = [{"data": [{"index": 0, "embedding": [0.4, 0.5]}]}]

    embedder = JinaEmbeddingFunction()
    embedder(["hello"])

    assert DummyClient.last_headers["Authorization"] == "Bearer env-jina"


def test_jina_embedding_requires_key(monkeypatch):
    _install_dummy_httpx(monkeypatch)
    monkeypatch.delenv("JINA_API_KEY", raising=False)

    with pytest.raises(ValueError, match="Jina API key not provided"):
        JinaEmbeddingFunction()


def test_jina_embedding_build_from_config(monkeypatch):
    _install_dummy_httpx(monkeypatch)
    monkeypatch.setenv("JINA_TOKEN", "config-jina")
    DummyClient.responses = [{"data": [{"index": 0, "embedding": [0.4, 0.5]}]}]

    embedder = JinaEmbeddingFunction.build_from_config(
        {"model_name": "test-model", "api_key_env_var": "JINA_TOKEN"}
    )
    embedder(["hello"])

    assert DummyClient.last_headers["Authorization"] == "Bearer config-jina"


def test_voyage_embedding_explicit_key_overrides_env(monkeypatch):
    class DummyVoyageClient:
        def __init__(self, api_key):
            self.api_key = api_key

        def embed(self, **kwargs):
            return types.SimpleNamespace(embeddings=[[0.7, 0.8]])

    dummy_voyageai = types.SimpleNamespace(Client=DummyVoyageClient)
    monkeypatch.setitem(__import__("sys").modules, "voyageai", dummy_voyageai)
    monkeypatch.setenv("VOYAGE_API_KEY", "env-voyage")

    embedder = VoyageAIEmbeddingFunction(api_key="explicit-voyage")
    result = embedder(["hello"])

    assert embedder._client.api_key == "explicit-voyage"
    assert result[0] == pytest.approx([0.7, 0.8])


def test_voyage_embedding_env_fallback(monkeypatch):
    class DummyVoyageClient:
        def __init__(self, api_key):
            self.api_key = api_key

        def embed(self, **kwargs):
            return types.SimpleNamespace(embeddings=[[0.7, 0.8]])

    dummy_voyageai = types.SimpleNamespace(Client=DummyVoyageClient)
    monkeypatch.setitem(__import__("sys").modules, "voyageai", dummy_voyageai)
    monkeypatch.setenv("VOYAGE_API_KEY", "env-voyage")

    embedder = VoyageAIEmbeddingFunction()
    embedder(["hello"])

    assert embedder._client.api_key == "env-voyage"


def test_voyage_embedding_requires_key(monkeypatch):
    dummy_voyageai = types.SimpleNamespace(Client=lambda api_key: None)
    monkeypatch.setitem(__import__("sys").modules, "voyageai", dummy_voyageai)
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)

    with pytest.raises(ValueError, match="Voyage API key not provided"):
        VoyageAIEmbeddingFunction()


def test_voyage_embedding_build_from_config(monkeypatch):
    class DummyVoyageClient:
        def __init__(self, api_key):
            self.api_key = api_key

        def embed(self, **kwargs):
            return types.SimpleNamespace(embeddings=[[0.7, 0.8]])

    dummy_voyageai = types.SimpleNamespace(Client=DummyVoyageClient)
    monkeypatch.setitem(__import__("sys").modules, "voyageai", dummy_voyageai)
    monkeypatch.setenv("VOYAGE_TOKEN", "config-voyage")

    embedder = VoyageAIEmbeddingFunction.build_from_config(
        {"model_name": "test-model", "api_key_env_var": "VOYAGE_TOKEN"}
    )
    embedder(["hello"])

    assert embedder._client.api_key == "config-voyage"


def test_mistral_embedding_explicit_key_overrides_env(monkeypatch):
    class DummyMistral:
        def __init__(self, api_key):
            self.api_key = api_key

        class embeddings:
            @staticmethod
            def create(**kwargs):
                return types.SimpleNamespace(data=[types.SimpleNamespace(embedding=[0.9, 1.0])])

    dummy_mistral = types.SimpleNamespace(Mistral=DummyMistral)
    monkeypatch.setitem(__import__("sys").modules, "mistralai", dummy_mistral)
    monkeypatch.setenv("MISTRAL_API_KEY", "env-mistral")

    embedder = MistralEmbeddingFunction(api_key="explicit-mistral")
    result = embedder(["hello"])

    assert embedder._client.api_key == "explicit-mistral"
    assert result[0] == pytest.approx([0.9, 1.0])


def test_mistral_embedding_env_fallback(monkeypatch):
    class DummyMistral:
        def __init__(self, api_key):
            self.api_key = api_key

        class embeddings:
            @staticmethod
            def create(**kwargs):
                return types.SimpleNamespace(data=[types.SimpleNamespace(embedding=[0.9, 1.0])])

    dummy_mistral = types.SimpleNamespace(Mistral=DummyMistral)
    monkeypatch.setitem(__import__("sys").modules, "mistralai", dummy_mistral)
    monkeypatch.setenv("MISTRAL_API_KEY", "env-mistral")

    embedder = MistralEmbeddingFunction()
    embedder(["hello"])

    assert embedder._client.api_key == "env-mistral"


def test_mistral_embedding_requires_key(monkeypatch):
    dummy_mistral = types.SimpleNamespace(Mistral=lambda api_key: None)
    monkeypatch.setitem(__import__("sys").modules, "mistralai", dummy_mistral)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)

    with pytest.raises(ValueError, match="Mistral API key not provided"):
        MistralEmbeddingFunction()


def test_mistral_embedding_build_from_config(monkeypatch):
    class DummyMistral:
        def __init__(self, api_key):
            self.api_key = api_key

        class embeddings:
            @staticmethod
            def create(**kwargs):
                return types.SimpleNamespace(data=[types.SimpleNamespace(embedding=[0.9, 1.0])])

    dummy_mistral = types.SimpleNamespace(Mistral=DummyMistral)
    monkeypatch.setitem(__import__("sys").modules, "mistralai", dummy_mistral)
    monkeypatch.setenv("MISTRAL_TOKEN", "config-mistral")

    embedder = MistralEmbeddingFunction.build_from_config(
        {"model": "test-model", "api_key_env_var": "MISTRAL_TOKEN"}
    )
    embedder(["hello"])

    assert embedder._client.api_key == "config-mistral"


def _install_dummy_google_genai(monkeypatch):
    class DummyEmbeddings:
        def __init__(self, values):
            self.values = values

    class DummyModels:
        def embed_content(self, **kwargs):
            return types.SimpleNamespace(embeddings=[DummyEmbeddings([0.3, 0.4])])

    class DummyClient:
        def __init__(self, api_key, vertexai=None, project=None, location=None):
            self.api_key = api_key
            self.vertexai = vertexai
            self.project = project
            self.location = location
            self.models = DummyModels()

    google_mod = types.ModuleType("google")
    genai_mod = types.SimpleNamespace(Client=DummyClient)
    monkeypatch.setitem(__import__("sys").modules, "google", google_mod)
    monkeypatch.setitem(__import__("sys").modules, "google.genai", genai_mod)


def test_google_genai_explicit_key_overrides_env(monkeypatch):
    _install_dummy_google_genai(monkeypatch)
    monkeypatch.setenv("GOOGLE_API_KEY", "env-google")

    embedder = GoogleGenAIEmbeddingFunction(api_key="explicit-google")
    result = embedder(["hello"])

    assert embedder._client.api_key == "explicit-google"
    assert result[0] == pytest.approx([0.3, 0.4])


def test_google_genai_env_fallback(monkeypatch):
    _install_dummy_google_genai(monkeypatch)
    monkeypatch.setenv("GOOGLE_API_KEY", "env-google")

    embedder = GoogleGenAIEmbeddingFunction()
    embedder(["hello"])

    assert embedder._client.api_key == "env-google"


def test_google_genai_requires_key(monkeypatch):
    _install_dummy_google_genai(monkeypatch)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with pytest.raises(ValueError, match="Google GenAI API key not provided"):
        GoogleGenAIEmbeddingFunction()


def test_google_genai_build_from_config(monkeypatch):
    _install_dummy_google_genai(monkeypatch)
    monkeypatch.setenv("GOOGLE_TOKEN", "config-google")

    embedder = GoogleGenAIEmbeddingFunction.build_from_config(
        {"model_name": "test-model", "api_key_env_var": "GOOGLE_TOKEN"}
    )
    embedder(["hello"])

    assert embedder._client.api_key == "config-google"


def test_tensorflow_hub_embedding_load_and_call(monkeypatch):
    class DummyHubModel:
        def __call__(self, inputs):
            return [[0.1, 0.2], [0.3, 0.4]]

    dummy_hub = types.SimpleNamespace(load=lambda url: DummyHubModel())
    monkeypatch.setitem(__import__("sys").modules, "tensorflow_hub", dummy_hub)

    embedder = TensorFlowHubEmbeddingFunction(model_url="https://tfhub.dev/mock")
    result = embedder(["a", "b"])

    assert result[0] == pytest.approx([0.1, 0.2])
    assert result[1] == pytest.approx([0.3, 0.4])


def test_together_ai_embedding_explicit_key_overrides_env(monkeypatch):
    _install_dummy_httpx(monkeypatch)
    monkeypatch.setenv("TOGETHER_API_KEY", "env-together")
    DummyClient.responses = [{"data": [{"embedding": [0.6, 0.7]}]}]

    embedder = TogetherAIEmbeddingFunction(api_key="explicit-together")
    result = embedder(["hello"])

    assert DummyClient.last_headers["Authorization"] == "Bearer explicit-together"
    assert result[0] == pytest.approx([0.6, 0.7])


def test_together_ai_embedding_env_fallback(monkeypatch):
    _install_dummy_httpx(monkeypatch)
    monkeypatch.setenv("TOGETHER_API_KEY", "env-together")
    DummyClient.responses = [{"data": [{"embedding": [0.6, 0.7]}]}]

    embedder = TogetherAIEmbeddingFunction()
    embedder(["hello"])

    assert DummyClient.last_headers["Authorization"] == "Bearer env-together"


def test_together_ai_embedding_requires_key(monkeypatch):
    _install_dummy_httpx(monkeypatch)
    monkeypatch.delenv("TOGETHER_API_KEY", raising=False)

    with pytest.raises(ValueError, match="Together API key not provided"):
        TogetherAIEmbeddingFunction()


def test_together_ai_embedding_build_from_config(monkeypatch):
    _install_dummy_httpx(monkeypatch)
    monkeypatch.setenv("TOGETHER_TOKEN", "config-together")
    DummyClient.responses = [{"data": [{"embedding": [0.6, 0.7]}]}]

    embedder = TogetherAIEmbeddingFunction.build_from_config(
        {"model_name": "test-model", "api_key_env_var": "TOGETHER_TOKEN"}
    )
    embedder(["hello"])

    assert DummyClient.last_headers["Authorization"] == "Bearer config-together"
