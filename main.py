import csv
import xml.etree.ElementTree as ET
import requests
from importlib.metadata import distribution
import yaml


def read_pom_file(file_path):
    dependencies = []

    # Parse XML file
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Find dependencies
    for dependency in root.findall('.//{http://maven.apache.org/POM/4.0.0}dependency'):
        group_id = dependency.find('{http://maven.apache.org/POM/4.0.0}groupId').text
        artifact_id = dependency.find('{http://maven.apache.org/POM/4.0.0}artifactId').text

        # Get the current stable version from Maven Central
        stable_version = get_stable_version_maven(group_id, artifact_id)

        recommendation = ''
        if stable_version and stable_version != dependency.find('{http://maven.apache.org/POM/4.0.0}version').text:
            recommendation = f"Upgrade {group_id}:{artifact_id} from {dependency.find('{http://maven.apache.org/POM/4.0.0}version').text} to {stable_version}"

        dependencies.append({
            'group_id': group_id,
            'artifact_id': artifact_id,
            'old_version': dependency.find('{http://maven.apache.org/POM/4.0.0}version').text,
            'new_version': stable_version if stable_version else 'Not found',
            'recommendation': recommendation
        })

    return dependencies


def read_requirements_file(file_path):
    dependencies = []

    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                dependency = line.split('==')
                package_name = dependency[0]

                # Get the current stable version from PyPI
                stable_version = get_stable_version_pip(package_name)

                recommendation = ''
                if stable_version and stable_version != dependency[1]:
                    recommendation = f"Upgrade {package_name} from {dependency[1]} to {stable_version}"

                dependencies.append({
                    'package_name': package_name,
                    'old_version': dependency[1] if len(dependency) > 1 else 'Not specified',
                    'new_version': stable_version if stable_version else 'Not found',
                    'recommendation': recommendation
                })

    return dependencies


def read_gemfile(file_path):
    dependencies = []

    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if line.startswith("gem"):
                parts = line.split("'")
                if len(parts) >= 2:
                    gem_name = parts[1]
                    if len(parts) >= 4:
                        stable_version = get_stable_version_gem(gem_name)
                        recommendation = ''
                        if stable_version and stable_version != parts[3]:
                            recommendation = f"Upgrade {gem_name} from {parts[3]} to {stable_version}"

                        dependencies.append({
                            'gem_name': gem_name,
                            'old_version': parts[3] if len(parts) > 3 else 'Not specified',
                            'new_version': stable_version if stable_version else 'Not found',
                            'recommendation': recommendation
                        })
                    else:
                        print(f"Warning: No version specified for {gem_name}.")
                else:
                    print(f"Warning: Malformed line in Gemfile - {line}")

    return dependencies


def get_stable_version_maven(group_id, artifact_id):
    # Construct Maven Central URL
    url = f"https://search.maven.org/solrsearch/select?q=g:\"{group_id}\"+AND+a:\"{artifact_id}\"&core=gav&rows=20&wt=json"

    # Fetch data from Maven Central
    response = requests.get(url)
    data = response.json()

    # Extract stable version from response
    if data['response']['numFound'] > 0:
        latest_version = data['response']['docs'][0]['v']
        return latest_version
    else:
        return None

def get_stable_version_pip(package_name):
    # Construct PyPI JSON API URL
    url = f"https://pypi.org/pypi/{package_name}/json"

    # Fetch data from PyPI
    response = requests.get(url)

    # Check if the package exists
    if response.status_code == 200:
        data = response.json()
        # Extract stable version from the JSON response
        return data["info"]["version"]
    else:
        return None


def get_stable_version_gem(gem_name):
    # Construct RubyGems API URL
    url = f"https://rubygems.org/api/v1/versions/{gem_name}.json"

    # Fetch data from RubyGems
    response = requests.get(url)
    data = response.json()

    # Extract stable version from response
    if data:
        # Filtering out non-integer characters from version strings
        versions = [version['number'] for version in data]
        filtered_versions = [v for v in versions if all(c.isdigit() or c == '.' for c in v)]

        # Selecting the latest version after filtering
        if filtered_versions:
            stable_version = max(filtered_versions, key=lambda v: tuple(map(int, v.split('.'))))
            return stable_version
    return None

def read_build_gradle(file_path):
    dependencies = []

    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if line.startswith("implementation"):
                parts = line.split("'")
                group_id = parts[1]
                artifact_id = parts[3]
                if len(parts) >= 6:
                    stable_version = get_stable_version_gradle(group_id, artifact_id)
                    recommendation = ''
                    if stable_version and stable_version != parts[5]:
                        recommendation = f"Upgrade {group_id}:{artifact_id} from {parts[5]} to {stable_version}"

                    dependencies.append({
                        'group_id': group_id,
                        'artifact_id': artifact_id,
                        'old_version': parts[5] if len(parts) > 5 else 'Not specified',
                        'new_version': stable_version if stable_version else 'Not found',
                        'recommendation': recommendation
                    })
                else:
                    print(f"Warning: No version specified for {group_id}:{artifact_id}.")

    return dependencies


def get_stable_version_gradle(group_id, artifact_id):
    # Construct Maven Central URL
    url = f"https://search.maven.org/solrsearch/select?q=g:\"{group_id}\"+AND+a:\"{artifact_id}\"&core=gav&rows=20&wt=json"

    # Fetch data from Maven Central
    response = requests.get(url)
    data = response.json()

    # Extract stable version from response
    if data['response']['numFound'] > 0:
        latest_version = data['response']['docs'][0]['v']
        return latest_version
    else:
        return None

def read_yaml_file(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)

    dependencies = []
    for dependency in data.get('dependencies', []):
        if 'name' in dependency:
            name = dependency['name']
            if 'version' in dependency:
                stable_version = get_stable_version_gem(name)
                recommendation = ''
                if stable_version and stable_version != dependency['version']:
                    recommendation = f"Upgrade {name} from {dependency['version']} to {stable_version}"

                dependencies.append({
                    'gem_name': name,
                    'old_version': dependency['version'],
                    'new_version': stable_version if stable_version else 'Not found',
                    'recommendation': recommendation
                })
            else:
                print(f"Warning: No version specified for {name} in the YAML file.")

    return dependencies


def write_to_csv(data, csv_file):
    with open(csv_file, 'w', newline='') as file:
        fieldnames = ['group_id', 'artifact_id', 'old_version', 'new_version', 'package_name', 'gem_name',
                      'recommendation']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


if __name__ == "__main__":
    pom_file = "pom.xml"
    requirements_file = "requirements.txt"
    gemfile = "Gemfile"
    build_gradle = "build.gradle"
    yaml_file = "travis.yaml"
    output_csv = "dependency_versions.csv"

    maven_dependencies = read_pom_file(pom_file)
    pip_dependencies = read_requirements_file(requirements_file)
    gem_dependencies = read_gemfile(gemfile)
    gradle_dependencies = read_build_gradle(build_gradle)
    # yaml_dependencies = read_yaml_file(yaml_file)

    all_dependencies = (
            maven_dependencies +
            pip_dependencies +
            gem_dependencies +
            gradle_dependencies
        # yaml_dependencies
    )
    write_to_csv(all_dependencies, output_csv)
