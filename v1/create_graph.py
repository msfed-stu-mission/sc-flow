from promptflow import tool
from promptflow.connections import CustomConnection, AzureOpenAIConnection
from azure.identity import DefaultAzureCredential
from azure.ai.ml.constants import AssetTypes, InputOutputModes
from azure.ai.ml import MLClient, Input, load_component
from azure.ai.ml.dsl import pipeline
import logging 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@tool
def create_graph(scg_dataset: str, 
                 dataset_version: str,
                 model_deployment: str,
                 embedding_deployment: str,
                 azureml_conn: CustomConnection,
                 neo4j_conn: CustomConnection,
                 aoai_conn: AzureOpenAIConnection) -> str:
    logger.info("Submitting graph job")

    ml_client = MLClient(workspace_name=azureml_conn.workspace_name,
                        resource_group_name=azureml_conn.resource_group,
                        subscription_id=azureml_conn.subscription_id,
                        credential = DefaultAzureCredential())

    graph_component = load_component(source="./graph_component/create_graph.yaml")
    scg_input = Input(path=f"azureml:{scg_dataset}:{dataset_version}", type=AssetTypes.URI_FILE, mode=InputOutputModes.RO_MOUNT)

    env_vars = {
        "AZURE_OPENAI_API_KEY": aoai_conn.api_key,
        "AZURE_OPENAI_ENDPOINT": aoai_conn.api_base,
        "AZURE_OPENAI_API_VERSION": aoai_conn.api_version,
        "MODEL_DEPLOYMENT": model_deployment,
        "EMBEDDING_DEPLOYMENT": embedding_deployment,

        "NEO4J_URI": neo4j_conn.neo4j_uri,
        "NEO4J_USERNAME": neo4j_conn.neo4j_username,
        "NEO4J_PASSWORD": neo4j_conn.neo4j_password,
        "NEO4J_DATABASE": neo4j_conn.neo4j_database,

        "AML_WORKSPACE_NAME": azureml_conn.workspace_name,
        "AML_RESOURCE_GROUP": azureml_conn.resource_group,
        "AML_SUBSCRIPTION_ID": azureml_conn.subscription_id,
    }

    @pipeline(
        default_compute="cpu-dev-cluster",
    )
    def create_scg_graph(pipeline_input_data):
        graph_node = graph_component(scg_dataset=pipeline_input_data)
        graph_node.environment_variables = env_vars

    pipeline_job = create_scg_graph(pipeline_input_data=scg_input)
    pipeline_job = ml_client.jobs.create_or_update(
        pipeline_job, experiment_name="create_scg_knowledge_graph"
    )
    return pipeline_job