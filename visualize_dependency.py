import os
import subprocess
import xml.etree.ElementTree as ET
from typing import Dict, List


def parse_xml_config(config_path: str) -> Dict[str, str]:
    """
    Parse the XML configuration file and return the necessary parameters.

    Args:
        config_path (str): Path to the XML configuration file.

    Returns:
        Dict[str, str]: A dictionary containing visualizer path, package name, max depth, and repository URL.
    """
    tree = ET.parse(config_path)
    root = tree.getroot()

    config = {
        "visualizer_path": root.find("visualizer_path").text,
        "package_name": root.find("package_name").text,
        "max_depth": int(root.find("max_depth").text),
        "repository_url": root.find("repository_url").text,
    }
    return config


def get_dependencies(package_name: str) -> List[str]:
    """
    Retrieve immediate package dependencies using pip.

    Args:
        package_name (str): The name of the package to retrieve dependencies for.

    Returns:
        List[str]: A list of dependencies for the given package.
    """
    try:
        result = subprocess.run(
            ["pip", "show", package_name], capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError:
        print(f"Error: Could not fetch dependencies for {package_name}")
        return []

    dependencies = []
    for line in result.stdout.splitlines():
        if line.startswith("Requires"):
            requires_line = line.split(":")[1].strip()  # Strip any extra spaces
            if requires_line:
                dependencies = [dep.strip() for dep in requires_line.split(", ") if dep]
            break
    return dependencies


def build_dependency_graph(package_name: str, max_depth: int) -> List[str]:
    """
    Recursively build the dependency graph for the package using PlantUML format.

    Args:
        package_name (str): The name of the package to build the dependency graph for.
        max_depth (int): The maximum depth of dependencies to traverse.

    Returns:
        List[str]: A list of strings representing the dependency relationships in PlantUML format.
    """
    graph = []
    visited = set()

    def add_dependencies(pkg_name: str, current_depth: int):
        if current_depth > max_depth or pkg_name in visited:
            return
        visited.add(pkg_name)

        dependencies = get_dependencies(pkg_name)
        for dep in dependencies:
            graph.append(f"{pkg_name} --> {dep}")
            add_dependencies(dep, current_depth + 1)

    add_dependencies(package_name, 1)
    return graph


def generate_plantuml_script(graph: List[str]) -> str:
    """
    Generate a PlantUML script based on the dependency graph.

    Args:
        graph (List[str]): The dependency graph as a list of strings.

    Returns:
        str: The generated PlantUML script.
    """
    plantuml_script = "@startuml\n"
    for relation in graph:
        plantuml_script += f"{relation}\n"
    plantuml_script += "@enduml"
    return plantuml_script


def save_plantuml_script(script: str, output_path: str) -> None:
    """
    Save the PlantUML script to a file.

    Args:
        script (str): The PlantUML script content.
        output_path (str): The file path where the script will be saved.
    """
    with open(output_path, "w") as f:
        f.write(script)


def visualize_graph(visualizer_path: str, script_path: str) -> None:
    """
    Visualize the graph using the specified PlantUML graph visualizer program.

    Args:
        visualizer_path (str): Path to the PlantUML jar file.
        script_path (str): Path to the PlantUML script to be visualized.
    """
    if not os.path.exists(visualizer_path):
        print(f"Error: Jar file not found at {visualizer_path}")
        return


def main(config_path: str) -> None:
    """
    Main function to build and visualize the dependency graph for a Python package.

    Args:
        config_path (str): Path to the XML configuration file.
    """
    config = parse_xml_config(config_path)
    package_name = config["package_name"]
    max_depth = config["max_depth"]
    visualizer_path = config["visualizer_path"]

    graph = build_dependency_graph(package_name, max_depth)

    plantuml_script = generate_plantuml_script(graph)

    script_path = "dependency_graph.puml"
    save_plantuml_script(plantuml_script, script_path)

    visualize_graph(visualizer_path, script_path)


if __name__ == "__main__":
    config_path = "config.xml"  # Path to your XML config file
    main(config_path)
