from datetime import datetime
from marshmallow import Schema, fields, validate, post_load

def validate_phone(value):
    pass

class CustomerCallSchema(Schema):
    timestamp = fields.DateTime(
        required=True,
        format="iso",
        metadata={"description": "Time the call was recorded"}
    )
    full_name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=100)
    )
    phone_number = fields.Str(
        required=False,
        validate=validate_phone
    )
    email = fields.Str(required=False)
    address = fields.Str(required=False)
    reason_calling = fields.Str(required=True)
    preferred_contact_method = fields.Str(
        required=True,
        validate=validate.OneOf(["Whatsapp", "Email", "Phone"])
    )
    
    additional_notes = fields.Str(required=False)

    @post_load
    def make_object(self, data, **kwargs):
        """Convert dict to Python object (optional)."""
        return CustomerCall(**data)

class CustomerCall:
    def __init__(self, timestamp: datetime, full_name: str, reason_calling: str, preferred_contact_method: str, 
                 phone_number: str = None, email: str = None, address: str = None, additional_notes: str = None):
        self.timestamp = timestamp
        self.full_name = full_name
        self.phone_number = phone_number
        self.email = email
        self.address = address
        self.reason_calling = reason_calling
        self.preferred_contact_method = preferred_contact_method
        self.additional_notes = additional_notes
        
    def __repr__(self):
        phone_display = self.phone_number if self.phone_number else "No phone"
        return f"<CustomerCall(name={self.full_name}, phone={phone_display})>"