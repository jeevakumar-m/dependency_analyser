from flask import Flask, render_template, request, jsonify
import csv
import xml.etree.ElementTree as ET
import requests
import yaml

app = Flask(__name__)


def read_pom_file(file):
    dependencies = []
    tree = ET.parse(file)
    root = tree.getroot()
    for dependency in root.findall('.//{http://maven.apache.org/POM/4.0.0}dependency'):
        group_id = dependency.find('{http://maven.apache.org/POM/4.0.0}groupId').text
        artifact_id = dependency.find('{http://maven.apache.org/POM/4.0.0}artifactId').text
        current_version = dependency.find('{http://maven.apache.org/POM/4.0.0}version').text
        dependencies.append((group_id, artifact_id,current_version))
    return dependencies


def read_requirements_file(file):
    dependencies = []
    for line in file:
        line = line.strip()
        if line and not line.startswith(b"#"):
            line = line.decode('utf-8')  # Decode bytes to string
            dependency = line.split('==')
            if len(dependency) > 1:
                dependencies.append((dependency[0], dependency[1]))
            else:
                dependencies.append((dependency[0], ''))
    return dependencies


def read_gemfile(file):
    dependencies = []
    for line in file:
        line = line.strip()
        if line.startswith("gem"):
            parts = line.split("'")
            if len(parts) >= 2:
                dependencies.append((parts[1], parts[3]))
    return dependencies


def read_build_gradle(file):
    dependencies = []
    for line in file:
        line = line.strip()
        if line.startswith(b"implementation"):
            line = line.decode('utf-8')  # Decode bytes to string
            parts = line.split("'")
            if len(parts) >= 6:
                dependencies.append((parts[1], parts[3], parts[5]))
    return dependencies


def get_stable_version_maven(group_id, artifact_id):
    url = f"https://search.maven.org/solrsearch/select?q=g:\"{group_id}\"+AND+a:\"{artifact_id}\"&core=gav&rows=20&wt=json"
    response = requests.get(url)
    data = response.json()
    if data['response']['numFound'] > 0:
        latest_version = data['response']['docs'][0]['v']
        return latest_version
    else:
        return None


def get_stable_version_pip(package_name):
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data["info"]["version"]
    else:
        return None


def get_stable_version_gem(gem_name):
    url = f"https://rubygems.org/api/v1/versions/{gem_name}.json"
    response = requests.get(url)
    data = response.json()
    if data:
        versions = [version['number'] for version in data]
        filtered_versions = [v for v in versions if all(c.isdigit() or c == '.' for c in v)]
        if filtered_versions:
            stable_version = max(filtered_versions, key=lambda v: tuple(map(int, v.split('.'))))
            return stable_version
    return None


def get_stable_version_gradle(group_id, artifact_id):
    url = f"https://search.maven.org/solrsearch/select?q=g:\"{group_id}\"+AND+a:\"{artifact_id}\"&core=gav&rows=20&wt=json"
    response = requests.get(url)
    data = response.json()
    if data['response']['numFound'] > 0:
        latest_version = data['response']['docs'][0]['v']
        return latest_version
    else:
        return None


def read_yaml_file(file):
    data = yaml.safe_load(file)
    dependencies = []
    for dependency in data.get('dependencies', []):
        if 'name' in dependency:
            name = dependency['name']
            version = dependency.get('version', '')
            dependencies.append((name, version))
    return dependencies


def write_to_csv(data, csv_file):
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Group ID', 'Artifact ID', 'Old Version', 'New Version', 'Recommendation'])
        for row in data:
            writer.writerow(row)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process', methods=['POST'])
def process():
    all_dependencies = []

    # Process POM.xml file
    pom_file = request.files['pom_file']
    if pom_file.filename.endswith('.xml'):
        all_dependencies.extend(process_pom_file(pom_file))

    # Process requirements.txt file
    requirements_file = request.files['requirements_file']
    if requirements_file.filename.endswith('.txt'):
        all_dependencies.extend(process_requirements_file(requirements_file))

    # Process Gemfile
    gemfile = request.files['gemfile']
    if gemfile.filename.endswith('.gemfile'):
        all_dependencies.extend(process_gemfile(gemfile))

    # Process build.gradle file
    build_gradle = request.files['build_gradle']
    if build_gradle.filename.endswith('.gradle'):
        all_dependencies.extend(process_build_gradle(build_gradle))

    return jsonify(all_dependencies)


def process_pom_file(file):
    dependencies = read_pom_file(file)
    processed_dependencies = []
    for group_id, artifact_id,current_version in dependencies:
        stable_version = get_stable_version_maven(group_id, artifact_id)
        if stable_version:
            processed_dependencies.append((group_id, artifact_id, current_version, stable_version))
    return processed_dependencies


def process_requirements_file(file):
    dependencies = read_requirements_file(file)
    processed_dependencies = []
    for package_name, old_version in dependencies:
        stable_version = get_stable_version_pip(package_name)
        if stable_version:
            processed_dependencies.append((package_name,'', old_version,stable_version))
    return processed_dependencies


def process_gemfile(file):
    dependencies = read_gemfile(file)
    processed_dependencies = []
    for gem_name, old_version in dependencies:
        stable_version = get_stable_version_gem(gem_name)
        if stable_version:
            processed_dependencies.append((gem_name, '',old_version, stable_version))
    return processed_dependencies


def process_build_gradle(file):
    dependencies = read_build_gradle(file)
    processed_dependencies = []
    for group_id, artifact_id, old_version in dependencies:
        stable_version = get_stable_version_gradle(group_id, artifact_id)
        if stable_version:
            processed_dependencies.append((group_id, artifact_id, old_version, stable_version))
    return processed_dependencies


if __name__ == "__main__":
    app.run(debug=True)
