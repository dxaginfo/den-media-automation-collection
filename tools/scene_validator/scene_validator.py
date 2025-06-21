#!/usr/bin/env python3
"""
SceneValidator - A tool for validating scene structure and composition in media production.

This tool uses Gemini API and Google Cloud Storage to validate scene elements against
defined rules and standards, ensuring technical and creative consistency.
"""

import os
import json
import logging
import argparse
from typing import Dict, List, Any, Union, Optional

# Third-party imports
try:
    import google.generativeai as genai
    from google.cloud import storage
    from google.oauth2 import service_account
except ImportError:
    print("Required packages not found. Installing...")
    import subprocess
    subprocess.check_call(["pip", "install", "google-generativeai", "google-cloud-storage"])
    import google.generativeai as genai
    from google.cloud import storage
    from google.oauth2 import service_account

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SceneValidator:
    """
    A class to validate scene structure and composition in media production.
    
    This tool checks for continuity errors, technical compliance,
    and adherence to creative guidelines.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 service_account_path: Optional[str] = None,
                 rules_path: Optional[str] = None):
        """
        Initialize the SceneValidator.
        
        Args:
            api_key: Gemini API key. If not provided, will look for GEMINI_API_KEY env var
            service_account_path: Path to Google Cloud service account JSON
            rules_path: Path to validation rules JSON file
        """
        # Initialize Gemini API
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required. Provide it as an argument or set GEMINI_API_KEY env var.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Initialize Google Cloud Storage if credentials are provided
        self.storage_client = None
        if service_account_path:
            credentials = service_account.Credentials.from_service_account_file(service_account_path)
            self.storage_client = storage.Client(credentials=credentials)
        
        # Load validation rules
        self.rules = self._load_rules(rules_path)
        
        logger.info("SceneValidator initialized successfully")
    
    def _load_rules(self, rules_path: Optional[str]) -> Dict[str, Any]:
        """
        Load validation rules from a JSON file or use defaults.
        
        Args:
            rules_path: Path to rules JSON file
            
        Returns:
            Dict containing validation rules
        """
        default_rules = {
            "technical": {
                "resolution": ["1920x1080", "3840x2160", "4096x2160"],
                "frameRate": [24, 25, 30, 60],
                "colorSpace": ["Rec.709", "Rec.2020", "DCI-P3"],
                "audioChannels": [2, 5.1, 7.1],
                "audioSampleRate": [48000, 96000]
            },
            "composition": {
                "enforceRuleOfThirds": True,
                "enforceHeadroom": True,
                "enforceLeadingSpace": True
            },
            "continuity": {
                "checkProps": True,
                "checkWardrobe": True,
                "checkLighting": True,
                "checkTimeOfDay": True
            }
        }
        
        if not rules_path:
            logger.info("No rules file provided. Using default rules.")
            return default_rules
        
        try:
            with open(rules_path, 'r') as f:
                custom_rules = json.load(f)
                # Merge with defaults to ensure all fields exist
                for section in default_rules:
                    if section in custom_rules:
                        for key in default_rules[section]:
                            if key not in custom_rules[section]:
                                custom_rules[section][key] = default_rules[section][key]
                    else:
                        custom_rules[section] = default_rules[section]
                
                logger.info(f"Loaded custom rules from {rules_path}")
                return custom_rules
        except Exception as e:
            logger.error(f"Error loading rules file: {e}")
            logger.info("Using default rules instead.")
            return default_rules
    
    def validate_scene_json(self, scene_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a scene defined in JSON format.
        
        Args:
            scene_data: Dictionary containing scene definition
            
        Returns:
            Dictionary with validation results
        """
        # Check for required fields
        required_fields = ["sceneName", "sceneNumber", "location", "timeOfDay", "characters", "props"]
        missing_fields = [field for field in required_fields if field not in scene_data]
        
        if missing_fields:
            return {
                "valid": False,
                "errors": [f"Missing required fields: {', '.join(missing_fields)}"],
                "warnings": []
            }
        
        errors = []
        warnings = []
        
        # Validate technical specifications if provided
        if "technical" in scene_data:
            tech = scene_data["technical"]
            tech_rules = self.rules["technical"]
            
            if "resolution" in tech and tech["resolution"] not in tech_rules["resolution"]:
                errors.append(f"Invalid resolution: {tech['resolution']}. Must be one of {tech_rules['resolution']}")
                
            if "frameRate" in tech and tech["frameRate"] not in tech_rules["frameRate"]:
                errors.append(f"Invalid frame rate: {tech['frameRate']}. Must be one of {tech_rules['frameRate']}")
                
            if "colorSpace" in tech and tech["colorSpace"] not in tech_rules["colorSpace"]:
                errors.append(f"Invalid color space: {tech['colorSpace']}. Must be one of {tech_rules['colorSpace']}")
        
        # Validate composition
        if "composition" in scene_data and self.rules["composition"]["enforceRuleOfThirds"]:
            comp = scene_data["composition"]
            if "ruleOfThirds" in comp and not comp["ruleOfThirds"]:
                warnings.append("Scene does not follow rule of thirds")
        
        # Validate continuity with Gemini API
        if self.rules["continuity"]["checkProps"] and len(scene_data.get("previousScenes", [])) > 0:
            prompt = f"""
            Analyze continuity between this scene and previous scenes.
            
            Current scene: {json.dumps(scene_data, indent=2)}
            
            Previous scenes: {json.dumps(scene_data.get('previousScenes', []), indent=2)}
            
            Check for continuity errors in props, wardrobe, lighting, and time of day.
            Return a JSON object with these fields:
            - continuityErrors: array of specific continuity errors found
            - continuityWarnings: array of potential continuity issues that should be reviewed
            """
            
            try:
                response = self.model.generate_content(prompt)
                continuity_analysis = json.loads(response.text)
                
                if "continuityErrors" in continuity_analysis and continuity_analysis["continuityErrors"]:
                    errors.extend(continuity_analysis["continuityErrors"])
                    
                if "continuityWarnings" in continuity_analysis and continuity_analysis["continuityWarnings"]:
                    warnings.extend(continuity_analysis["continuityWarnings"])
            except Exception as e:
                logger.error(f"Error analyzing continuity with Gemini API: {e}")
                warnings.append("Could not perform automated continuity check")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def validate_scene_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate a scene from a JSON file.
        
        Args:
            file_path: Path to JSON file containing scene data
            
        Returns:
            Dictionary with validation results
        """
        try:
            with open(file_path, 'r') as f:
                scene_data = json.load(f)
                logger.info(f"Loaded scene data from {file_path}")
                return self.validate_scene_json(scene_data)
        except Exception as e:
            logger.error(f"Error loading scene file: {e}")
            return {
                "valid": False,
                "errors": [f"Could not load scene file: {str(e)}"],
                "warnings": []
            }
    
    def validate_scene_from_gcs(self, bucket_name: str, blob_name: str) -> Dict[str, Any]:
        """
        Validate a scene from a Google Cloud Storage file.
        
        Args:
            bucket_name: GCS bucket name
            blob_name: Path to JSON file in the bucket
            
        Returns:
            Dictionary with validation results
        """
        if not self.storage_client:
            return {
                "valid": False,
                "errors": ["Google Cloud Storage client not initialized"],
                "warnings": []
            }
        
        try:
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            content = blob.download_as_text()
            scene_data = json.loads(content)
            logger.info(f"Loaded scene data from gs://{bucket_name}/{blob_name}")
            return self.validate_scene_json(scene_data)
        except Exception as e:
            logger.error(f"Error loading scene from GCS: {e}")
            return {
                "valid": False,
                "errors": [f"Could not load scene from GCS: {str(e)}"],
                "warnings": []
            }
    
    def generate_report(self, validation_result: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        Generate a detailed validation report.
        
        Args:
            validation_result: Result from validate_scene methods
            output_path: Optional path to save the report
            
        Returns:
            Report text
        """
        # Create a detailed report
        report_lines = ["# Scene Validation Report", ""]
        
        if validation_result["valid"]:
            report_lines.append("## ✅ Scene is valid")
        else:
            report_lines.append("## ❌ Scene is invalid")
        
        report_lines.append("")
        
        if validation_result["errors"]:
            report_lines.append("## Errors")
            for error in validation_result["errors"]:
                report_lines.append(f"- {error}")
            report_lines.append("")
        
        if validation_result["warnings"]:
            report_lines.append("## Warnings")
            for warning in validation_result["warnings"]:
                report_lines.append(f"- {warning}")
            report_lines.append("")
        
        report_text = "\n".join(report_lines)
        
        if output_path:
            try:
                with open(output_path, 'w') as f:
                    f.write(report_text)
                logger.info(f"Saved validation report to {output_path}")
            except Exception as e:
                logger.error(f"Error saving report: {e}")
        
        return report_text

def main():
    """Command-line interface for the SceneValidator."""
    parser = argparse.ArgumentParser(description="Validate scene structure and composition")
    parser.add_argument("--scene-file", help="Path to scene JSON file")
    parser.add_argument("--gcs-bucket", help="Google Cloud Storage bucket name")
    parser.add_argument("--gcs-blob", help="Google Cloud Storage blob path")
    parser.add_argument("--rules-file", help="Path to validation rules JSON file")
    parser.add_argument("--api-key", help="Gemini API key (or set GEMINI_API_KEY env var)")
    parser.add_argument("--service-account", help="Path to Google Cloud service account JSON")
    parser.add_argument("--output", help="Output path for validation report")
    
    args = parser.parse_args()
    
    validator = SceneValidator(
        api_key=args.api_key,
        service_account_path=args.service_account,
        rules_path=args.rules_file
    )
    
    if args.scene_file:
        result = validator.validate_scene_file(args.scene_file)
    elif args.gcs_bucket and args.gcs_blob:
        result = validator.validate_scene_from_gcs(args.gcs_bucket, args.gcs_blob)
    else:
        print("Error: Either --scene-file or both --gcs-bucket and --gcs-blob are required")
        return
    
    report = validator.generate_report(result, args.output)
    print(report)

if __name__ == "__main__":
    main()