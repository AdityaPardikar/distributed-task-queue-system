"""Email template engine with Jinja2 rendering and variable validation"""

import re
from typing import Optional
from jinja2 import Template, TemplateSyntaxError, UndefinedError, Environment
from pydantic import BaseModel


class TemplateVariableInfo(BaseModel):
    """Information about template variables"""
    name: str
    required: bool
    default: Optional[str] = None


class EmailTemplate:
    """Jinja2-based email template with variable tracking"""

    def __init__(self, subject: str, body: str):
        """Initialize template with subject and body"""
        self.subject = subject
        self.body = body
        self.template_env = Environment()
        self._validate_syntax()

    def _validate_syntax(self) -> None:
        """Validate template syntax"""
        try:
            Template(self.subject)
            Template(self.body)
        except TemplateSyntaxError as e:
            raise ValueError(f"Template syntax error: {e.message}")

    def extract_variables(self) -> list[TemplateVariableInfo]:
        """Extract all variables used in templates"""
        variables = set()
        
        # Extract from subject and body using regex to find {{ var_name }} patterns
        pattern = r'{{\s*(\w+)\s*(?:\|[^}]*)?\s*}}'
        
        subject_vars = re.findall(pattern, self.subject)
        body_vars = re.findall(pattern, self.body)
        
        variables.update(subject_vars)
        variables.update(body_vars)
        
        # Return as list of TemplateVariableInfo objects
        return [TemplateVariableInfo(name=var, required=True) for var in sorted(variables)]

    def validate_variables(self, variables: dict) -> tuple[bool, list[str]]:
        """
        Validate that required variables are provided.
        
        Returns:
            (is_valid, list_of_missing_vars)
        """
        required_vars = {v.name for v in self.extract_variables()}
        provided_vars = set(variables.keys())
        missing = required_vars - provided_vars
        
        return len(missing) == 0, sorted(list(missing))

    def render(self, variables: dict) -> tuple[str, str]:
        """
        Render template with provided variables.
        
        Args:
            variables: Dict of variable values for template substitution
            
        Returns:
            (rendered_subject, rendered_body)
            
        Raises:
            ValueError: If required variables are missing or template rendering fails
        """
        is_valid, missing = self.validate_variables(variables)
        if not is_valid:
            raise ValueError(f"Missing required variables: {', '.join(missing)}")
        
        try:
            subject_tmpl = Template(self.subject)
            body_tmpl = Template(self.body)
            
            rendered_subject = subject_tmpl.render(**variables)
            rendered_body = body_tmpl.render(**variables)
            
            return rendered_subject, rendered_body
        except UndefinedError as e:
            raise ValueError(f"Template rendering error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected template error: {str(e)}")

    def render_with_defaults(self, variables: dict, defaults: Optional[dict] = None) -> tuple[str, str]:
        """
        Render template with variables and optional defaults.
        
        Args:
            variables: Provided variables
            defaults: Default values for missing variables
            
        Returns:
            (rendered_subject, rendered_body)
        """
        merged_vars = {**(defaults or {}), **variables}
        return self.render(merged_vars)
