import os

from zernio import Zernio
from config import ACCOUNT_ID,ZERNIO_API_KEY


client_zernio = Zernio(
    api_key=ZERNIO_API_KEY
)

# Step 1: Create a flow
response = client_zernio.whatsapp_flows.create_whats_app_flow(

    account_id='6a82f5dd77555aae0191b739',
    name='lead_capture_form',
    categories=['LEAD_GENERATION']
)
print(response)
flow_id = response.flow.id
