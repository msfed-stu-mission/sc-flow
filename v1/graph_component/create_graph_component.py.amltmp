import os
from pathlib import Path
from mldesigner import command_component, Input, Output

@command_component(
    name="build_scg_graph",
    version="1",
    display_name="Build SCG Knowledge Graph",
    description="Use GPT-4o to construct an entity-relationship graph from a Security Classification Guide",
    environment=dict(
        image=os.getenv("AZUREML_IMAGE"),
    ),
)
def build_scg_graph_component(scg_dataset: Input(type="uri_file")):
    from create_graph import create_graph
    create_graph(scg_dataset)