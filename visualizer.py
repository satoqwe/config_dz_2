import argparse
import subprocess
import os
import sys
import tempfile


def get_commits(repo_path, tag_name):
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "log", "--pretty=format:%H %P", tag_name],
            check=True, stdout=subprocess.PIPE, text=True
        )
        if not result.stdout.strip():
            print(f"No commits found for the tag '{tag_name}'.")
            sys.exit(1)

        commits = [line.split() for line in result.stdout.strip().split("\n")]
        return commits

    except subprocess.CalledProcessError as e:
        print("Error executing git log:", e)
        sys.exit(1)


def generate_plantuml(commits):
    """
    Сгенерировать текст PlantUML для графа зависимостей.
    """
    nodes = []
    edges = []

    for commit in commits:
        commit_hash = commit[0]
        parents = commit[1:]
        nodes.append(f'"{commit_hash}"')
        for parent in parents:
            edges.append(f'"{commit_hash}" --> "{parent}"')

    nodes_text = "\n".join(nodes)
    edges_text = "\n".join(edges)

    plantuml_content = f"@startuml\n{nodes_text}\n{edges_text}\n@enduml"
    return plantuml_content


def visualize_graph(plantuml_text, plantuml_path):
    """
    Сгенерировать графическое изображение с помощью PlantUML.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".puml") as puml_file:
        puml_file.write(plantuml_text.encode('utf-8'))
        puml_file_path = puml_file.name

    output_path = puml_file_path.replace(".puml", ".png")
    try:
        subprocess.run(["java", "-jar", plantuml_path, puml_file_path],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Граф успешно сгенерирован: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при генерации графа: {e.stderr.decode('utf-8')}")
    finally:
        os.remove(puml_file_path)


def main():
    parser = argparse.ArgumentParser(description="Визуализатор графа зависимостей коммитов.")
    parser.add_argument("--plantuml", required=True, help="Путь к программе PlantUML (например, plantuml.jar).")
    parser.add_argument("--repo", required=True, help="Путь к анализируемому репозиторию.")
    parser.add_argument("--tag", required=True, help="Имя тега в репозитории.")

    args = parser.parse_args()

    if not os.path.isfile(args.plantuml):
        print(f"Ошибка: PlantUML не найден по пути {args.plantuml}")
        sys.exit(1)

    if not os.path.isdir(os.path.join(args.repo, ".git")):
        print(f"Ошибка: Указанный путь {args.repo} не является Git-репозиторием.")
        sys.exit(1)

    commits = get_commits(args.repo, args.tag)
    plantuml_text = generate_plantuml(commits)
    visualize_graph(plantuml_text, args.plantuml)


if __name__ == "__main__":
    main()
