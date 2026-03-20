from prometheus_client import Counter, Histogram, start_http_server
import time

# Counters
dm_received_total = Counter(
    'dm_received_total',
    'Total number of Instagram DMs received',
    ['location']
)

booking_link_sent = Counter(
    'booking_link_sent_total',
    'Total number of booking links sent'
)

escalation_total = Counter(
    'escalation_total',
    'Total number of escalations to a human'
)

meta_api_errors_total = Counter(
    'meta_api_errors_total',
    'Total number of meta API errors'
)

bedrock_model_used = Counter(
    'bedrock_model_used_total',
    'Total number of bedrock models used',
    ['model']
)

# Histograms
dm_response_latency = Histogram(
    'dm_response_latency',
    'End-to-end DM response latency in seconds'
)

bedrock_latency = Histogram(
    'bedrock_api_latency_seconds',
    'Bedrock API call latency in seconds'
)

sheets_write_latency = Histogram(
    'sheets_write_latency_seconds',
    'Google Sheets write latency in seconds'
)


def track_dm_received(location: str = 'unknown'):
    """Increment DM received counter"""
    dm_received_total.labels(location=location).inc()

def track_booking_link_sent():
    """Increment booking link sent counter"""
    booking_link_sent.inc()

def track_escalation_total():
    """Increment escalation counter"""
    escalation_total.inc()

def track_meta_api_errors_total():
    """Increment meta API errors counter"""
    meta_api_errors_total.inc()

def track_bedrock_model(model_id: str):
    """Increment bedrock model counter"""
    bedrock_model_used.labels(model=model_id).inc()

def start_metrics_server(port: int= 8000):
    """Start metrics server"""
    start_http_server(port)