import os
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

class AIAssistant:
    def __init__(self, api_key=None, test_mode=False):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.test_mode = test_mode
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            
        logging.basicConfig(level=logging.INFO)
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                # Perform a lightweight health check
                self.client.models.list()
                self.enabled = True
            except Exception as e:
                logger.error("Failed to initialize OpenAI client", exc_info=e)
                self.client = None
                self.enabled = False
        else:
            self.client = None
            self.enabled = False
            logger.warning("OpenAI API key not found. AI Assistant functionality disabled.")
        else:
            self.client = None
            self.enabled = False
            logger.warning("OpenAI API key not found. AI Assistant functionality disabled.")
    
    def analyze_request_urgency(self, description, justification):
        """Analyze request text and suggest urgency level"""
        if not self.enabled or not self.client:
            return {"urgency": "Normal", "confidence": 0.5, "reasoning": "AI analysis unavailable"}
        
        try:
            prompt = f"""
            Analyze the following business request and determine the urgency level.
            
            Description: {description}
            Justification: {justification}
            
            Consider factors like:
            - Time sensitivity
            - Business impact
            - Financial implications
            - Safety concerns
            
            Respond with JSON in this format:
            {{"urgency": "Low|Normal|High|Critical", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {"role": "system", "content": "You are a business analysis expert. Analyze urgency levels for business requests."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content:
                result = json.loads(content)
                return result
            else:
                return {"urgency": "Normal", "confidence": 0.5, "reasoning": "No response from AI"}
            
        except Exception as e:
            logger.error(f"AI urgency analysis failed: {str(e)}")
            return {"urgency": "Normal", "confidence": 0.5, "reasoning": "Analysis failed"}
    
    def generate_approval_notes(self, request_type, item_name, amount, department):
        """Generate suggested approval notes for admin review"""
        if not self.enabled or not self.client:
            return "AI analysis unavailable. Please review manually."
        
        try:
            prompt = f"""
            Generate professional approval notes for a {request_type} request:
            
            Item/Purpose: {item_name}
            Amount: ${amount}
            Department: {department}
            
            Provide brief, professional notes covering:
            - Budget compliance
            - Business necessity
            - Approval recommendation
            
            Keep it concise and professional.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {"role": "system", "content": "You are a business approval specialist. Generate professional review notes."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.choices[0].message.content
            return content if content else "AI analysis unavailable. Please review manually."
            
        except Exception as e:
            logger.error(f"AI note generation failed: {str(e)}")
            return "AI analysis unavailable. Please review manually."
    
    def analyze_expense_patterns(self, expenses_data):
        """Analyze expense patterns and provide insights"""
        if not self.enabled or not self.client:
            return "AI analysis unavailable"
        
        try:
            prompt = f"""
            Analyze these expense patterns and provide business insights:
            
            {json.dumps(expenses_data, indent=2)}
            
            Provide insights on:
            - Spending trends
            - Unusual patterns
            - Cost optimization suggestions
            - Budget recommendations
            
            Keep analysis concise and actionable.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {"role": "system", "content": "You are a financial analyst. Analyze expense data and provide actionable insights."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.choices[0].message.content
            return content if content else "AI analysis unavailable"
            
        except Exception as e:
            logger.error(f"AI expense analysis failed: {str(e)}")
            return "AI analysis unavailable"

# Initialize AI assistant
ai_assistant = AIAssistant()

    def _extract_json(self, content):
        import re
        try:
            match = re.search(r'{.*}', content, re.DOTALL)
            if match:
                return json.loads(match.group())
            logger.warning("No valid JSON found in content")
        except Exception as e:
            logger.error("Error parsing JSON from content", exc_info=e)
        return {"error": "Invalid response format"}
