from twilio.rest import Client
from twilio.rest.api.v2010.account.call import CallInstance
from core.config.settings import settings
from data_types.twilio import CallStatus

class TwilioService:
    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    def get_call(self, call_sid: str) -> CallInstance:
        return self.client.calls(call_sid).fetch()
    
    def hangup_call(self, call_sid: str):
        return self.client.calls(call_sid).update(status=CallStatus.COMPLETED.value)
    

twilio_service = TwilioService()