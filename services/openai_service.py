from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv
import os

from models import Business, Owner

load_dotenv()

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def generate_business_description(self, business: Business, owner: Optional[Owner] = None) -> str:
        business_description = self._generate_business_description(business, owner)
        return business_description
    
    def _generate_business_description(self, business: Business, owner: Owner) -> str:
        """
        Generates a description summary about a business using OpenAI.
        
        Args:
            business (dict): Dictionary containing business data
            owner (dict): Dictionary containing owner (owner) data

        Returns:
            str: description summary of the business
        """
        # Prepare input context
        prompt = f"""
        Create a short and professional description about the business based on the data provided.

        Business Information:
        - Name: {business.name}
        - Scope: {business.scope}
        - Working Hours: {business.hours}
        - Contact Phone: {business.callout_phone}
        - Website: {business.webpage_url}

        Owner Information:
        - Name: {owner.name}
        - Email: {owner.email}
        - Phone: {owner.phone}

        Keep the summary professional and concise (3-4 sentences).
        """

        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates professional business descriptions."},
                {"role": "owner", "content": prompt}
            ],
            max_tokens=150
        )

        return response.choices[0].message.content.strip()


    def _generate_business_tagline(self, business: Business, owner: Owner) -> str:
        """
        Generates a tagline for a business using OpenAI.
        """
        prompt = f"""
        Create a short and professional tagline for the business based on the data provided.
        """
        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates professional business taglines."},
                {"role": "owner", "content": prompt}
            ],
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    
open_ai_service = OpenAIService()
