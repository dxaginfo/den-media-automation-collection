# SceneValidator Documentation

SceneValidator is a tool for validating scene structure and composition in media production. It uses Gemini API and Google Cloud Storage to validate scene elements against defined rules and standards, ensuring technical and creative consistency.

## Installation

```bash
# Clone the repository
git clone https://github.com/dxaginfo/den-media-automation-collection.git
cd den-media-automation-collection

# Install required packages
pip install -r requirements.txt
```

## Configuration

### API Keys

SceneValidator requires a Gemini API key to perform continuity checks. You can provide this in two ways:

1. As an environment variable:
   ```bash
   export GEMINI_API_KEY="your-api-key"
   ```

2. As a command-line argument:
   ```bash
   python tools/scene_validator/scene_validator.py --api-key "your-api-key" ...
   ```

### Google Cloud Storage (Optional)

For integration with Google Cloud Storage, you'll need a service account JSON file:

```bash
python tools/scene_validator/scene_validator.py --service-account "path/to/service-account.json" ...
```

### Validation Rules

SceneValidator uses a set of rules to validate scenes. Default rules are built in, but you can customize them by providing a JSON file:

```bash
python tools/scene_validator/scene_validator.py --rules-file "path/to/rules.json" ...
```

A sample rules file is provided in the `config` directory (`config/scene_validator_rules.json`).

## Usage

### Validating a Local Scene File

```bash
python tools/scene_validator/scene_validator.py --scene-file "path/to/scene.json"
```

### Validating a Scene from Google Cloud Storage

```bash
python tools/scene_validator/scene_validator.py --gcs-bucket "bucket-name" --gcs-blob "path/to/scene.json"
```

### Generating a Report

By default, the validation report is printed to the console. To save it to a file:

```bash
python tools/scene_validator/scene_validator.py --scene-file "path/to/scene.json" --output "report.md"
```

## Scene File Format

Scene files should be in JSON format with the following structure:

```json
{
  "sceneName": "Scene Name",
  "sceneNumber": "1A",
  "location": "Location Description",
  "timeOfDay": "Time of Day",
  "characters": [
    {
      "name": "Character Name",
      "wardrobe": "Wardrobe Description",
      "props": ["Prop 1", "Prop 2"]
    }
  ],
  "props": ["Prop 1", "Prop 2", "Prop 3"],
  "technical": {
    "resolution": "1920x1080",
    "frameRate": 24,
    "colorSpace": "Rec.709",
    "audioChannels": 2,
    "audioSampleRate": 48000
  },
  "composition": {
    "ruleOfThirds": true,
    "depthOfField": "Shallow",
    "framing": "Medium shot"
  },
  "previousScenes": [
    {
      // Previous scene data in the same format
    }
  ]
}
```

For continuity checks, include previous scenes in the `previousScenes` array.

## Validation Categories

SceneValidator performs checks in several categories:

### 1. Required Fields

Checks if all required fields are present:
- sceneName
- sceneNumber
- location
- timeOfDay
- characters
- props

### 2. Technical Validation

Checks technical specifications against allowed values:
- resolution
- frameRate
- colorSpace
- audioChannels
- audioSampleRate

### 3. Composition Validation

Checks compositional elements:
- Rule of thirds
- Headroom
- Leading space

### 4. Continuity Validation

Uses Gemini API to analyze continuity between scenes:
- Props consistency
- Wardrobe consistency
- Lighting consistency
- Time of day consistency

## Using as a Library

You can also use SceneValidator as a library in your Python code:

```python
from tools.scene_validator.scene_validator import SceneValidator

# Initialize with API key
validator = SceneValidator(api_key="your-api-key")

# Load scene data
scene_data = {
    "sceneName": "Café Scene",
    "sceneNumber": "1A",
    # ... other scene data
}

# Validate scene
result = validator.validate_scene_json(scene_data)

# Generate report
report = validator.generate_report(result)
print(report)
```

## Integration with Other Tools

SceneValidator works well with other tools in the collection:

- **ContinuityTracker**: For more detailed continuity tracking across an entire production
- **StoryboardGen**: To validate scene elements against storyboards
- **EnvironmentTagger**: To ensure consistent tagging of environments

## Examples

See the `examples/scene_validator` directory for sample scene files and usage examples.

## Troubleshooting

### Common Issues

1. **API Key Issues**: Make sure your Gemini API key is valid and accessible.

2. **JSON Parsing Errors**: Ensure your scene files are valid JSON with all required fields.

3. **Google Cloud Storage Access**: Verify that your service account has appropriate permissions.

### Logging

SceneValidator uses Python's logging module. To increase log verbosity:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.