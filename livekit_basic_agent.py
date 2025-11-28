"""
LiveKit Voice Agent - Quick Start
==================================
The simplest possible LiveKit voice agent to get you started.
Requires only OpenAI and Deepgram API keys.
"""
# Replace the import and TTS initialization:
#from coqui_tts import CoquiTTSPlugin
from edge_tts_plugin import EdgeTTSPlugin
from edge_tts_plugin import EdgeTTSPlugin
#from kittentts import KittenTTS
#from Kitten_tts import KittenTTSPlugin
#from chatterbox_tts import ChatterboxTTSPlugin
#from bark_tts import BarkTTSPlugin  # Add this import
#from super_fast_coqui_tts import SuperFastCoquiTTSPlugin
#from reliable_fast_coqui_tts import ReliableFastCoquiTTSPlugin
#from chatterbox_tts_plugin import ChatterboxTTSPlugin
#from xtts_v2_plugin import XTTSV2Plugin
#from realtime_tts_plugin import RealtimeTTSPlugin
#from realtime_tts_no_pyaudio import RealtimeTTSNoPyAudio
from livekit.plugins import minimax
#from kokoro_tts_plugin import KokoroTTSPlugin
#from kokoro_tts_plugin import KokoroTTS
#from kokoro_fastapi_tts import KokoroFastAPITTS

###############################################
"""
from kokoro_tts import KokoroTTS
from simple_tts import WorkingTTS
from simple_kokoro import SimpleKokoroTTS
from kokoro_tts_working import KokoroTTSReal
from kokoro_integration import KokoroTTSIntegration
from simple_kokoro_tts import WorkingTTSFinal
"""
###################################################
from livekit.plugins import cartesia
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentSession, RunContext
from livekit.agents.llm import function_tool
from livekit.plugins import openai, deepgram, silero
from datetime import datetime
from livekit.plugins import rime
import os
import logging
logger = logging.getLogger("voice-assistant")
# Load environment variables
load_dotenv(".env")

class Assistant(Agent):
    """Basic voice assistant with Health insurance claim capabilities."""

    def __init__(self):
        super().__init__(
            instructions="""SYSTEM:
                You are an empathetic and professional Voice AI Accident Claim Intake Agent for [Company Name].
                Your purpose is to collect client information for an accident injury claim.
                Ask one question at a time.
                Keep answers short and conversational.
                Do not provide legal advice.
                Never mention that you are AI.

                Tone:
                Warm, caring, respectful, short sentences.

                Conversation Flow:

                Greeting
                “Hello, my name is [Agent Name], and I'm calling from [Company Name]. How are you doing today?”
                Wait for response.

                Accident Intro
                “I'm really sorry to hear about your recent accident. We received a report from the road management company and it shows you may be entitled to compensation for your injuries.
                Is now a good time to quickly go through some details with you?”

                Information Gathering (ask in order):

                Full name & contact

                Date and location of accident

                Describe how accident happened

                Injuries

                Medical treatment

                Witnesses or report filed

                Vehicle registration (user + third party)

                Insurance company and whether incident is reported

                Photos available

                Reassurance
                “Thank you for sharing all that. Based on what you've told me, it does sound like you may have a valid claim. Our senior case manager will contact you within 24 hours. There are no upfront costs and everything will be explained clearly.”

                Closing
                “Before we finish, is there anything else about the accident you'd like us to know?”
                “Thank you for your time. Expect a call within 24 hours.”

                Behavior Rules:

                Acknowledge answers: “I understand,” “Thank you,” “I'm sorry that happened.”

                If unclear: “I didn't catch that, could you repeat it?”

                If user goes off-topic: gently and apologetically guide back.

                If user asks legal questions: “Our senior case manager will explain that for you.”

                Never skip questions.

                Never assume answers.

                Slot Filling:
                Internally track these fields:
                full_name, contact_number, accident_date, accident_location, accident_description, injuries, medical_treatment, witnesses_or_report, vehicle_registration_user, vehicle_registration_third_party, insurance_company, incident_reported, photos_available, additional_notes.
                Only move to the next question after the previous field is collected."""
        )

        # Mock Airbnb database
        self.airbnbs = {
            "san francisco": [
                {
                    "id": "sf001",
                    "name": "Cozy Downtown Loft",
                    "address": "123 Market Street, San Francisco, CA",
                    "price": 150,
                    "amenities": ["WiFi", "Kitchen", "Workspace"],
                },
                {
                    "id": "sf002",
                    "name": "Victorian House with Bay Views",
                    "address": "456 Castro Street, San Francisco, CA",
                    "price": 220,
                    "amenities": ["WiFi", "Parking", "Washer/Dryer", "Bay Views"],
                },
                {
                    "id": "sf003",
                    "name": "Modern Studio near Golden Gate",
                    "address": "789 Presidio Avenue, San Francisco, CA",
                    "price": 180,
                    "amenities": ["WiFi", "Kitchen", "Pet Friendly"],
                },
            ],
            "new york": [
                {
                    "id": "ny001",
                    "name": "Brooklyn Brownstone Apartment",
                    "address": "321 Bedford Avenue, Brooklyn, NY",
                    "price": 175,
                    "amenities": ["WiFi", "Kitchen", "Backyard Access"],
                },
                {
                    "id": "ny002",
                    "name": "Manhattan Skyline Penthouse",
                    "address": "555 Fifth Avenue, Manhattan, NY",
                    "price": 350,
                    "amenities": ["WiFi", "Gym", "Doorman", "City Views"],
                },
                {
                    "id": "ny003",
                    "name": "Artsy East Village Loft",
                    "address": "88 Avenue A, Manhattan, NY",
                    "price": 195,
                    "amenities": ["WiFi", "Washer/Dryer", "Exposed Brick"],
                },
            ],
            "los angeles": [
                {
                    "id": "la001",
                    "name": "Venice Beach Bungalow",
                    "address": "234 Ocean Front Walk, Venice, CA",
                    "price": 200,
                    "amenities": ["WiFi", "Beach Access", "Patio"],
                },
                {
                    "id": "la002",
                    "name": "Hollywood Hills Villa",
                    "address": "777 Mulholland Drive, Los Angeles, CA",
                    "price": 400,
                    "amenities": ["WiFi", "Pool", "City Views", "Hot Tub"],
                },
            ],
        }

        # Track bookings
        self.bookings = []

    @function_tool
    async def get_current_date_and_time(self, context: RunContext) -> str:
        """Get the current date and time."""
        current_datetime = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        return f"The current date and time is {current_datetime}"

    @function_tool
    async def search_airbnbs(self, context: RunContext, city: str) -> str:
        """Search for available Airbnbs in a city.

        Args:
            city: The city name to search for Airbnbs (e.g., 'San Francisco', 'New York', 'Los Angeles')
        """
        city_lower = city.lower()

        if city_lower not in self.airbnbs:
            return f"Sorry, I don't have any Airbnb listings for {city} at the moment. Available cities are: San Francisco, New York, and Los Angeles."

        listings = self.airbnbs[city_lower]
        result = f"Found {len(listings)} Airbnbs in {city}:\n\n"

        for listing in listings:
            result += f"• {listing['name']}\n"
            result += f"  Address: {listing['address']}\n"
            result += f"  Price: ${listing['price']} per night\n"
            result += f"  Amenities: {', '.join(listing['amenities'])}\n"
            result += f"  ID: {listing['id']}\n\n"

        return result

    @function_tool
    async def book_airbnb(self, context: RunContext, airbnb_id: str, guest_name: str, check_in_date: str, check_out_date: str) -> str:
        """Ask these questions.

        Args:
            airbnb_id: The ID of the Airbnb to book (e.g., 'sf001')
            guest_name: Name of the guest making the booking
            check_in_date: Check-in date (e.g., 'January 15, 2025')
            check_out_date: Check-out date (e.g., 'January 20, 2025')
        """
        # Find the Airbnb
        airbnb = None
        for city_listings in self.airbnbs.values():
            for listing in city_listings:
                if listing['id'] == airbnb_id:
                    airbnb = listing
                    break
            if airbnb:
                break

        if not airbnb:
            return f"Sorry, I couldn't find an Airbnb with ID {airbnb_id}. Please search for available listings first."

        # Create booking
        booking = {
            "confirmation_number": f"BK{len(self.bookings) + 1001}",
            "airbnb_name": airbnb['name'],
            "address": airbnb['address'],
            "guest_name": guest_name,
            "check_in": check_in_date,
            "check_out": check_out_date,
            "total_price": airbnb['price'],
        }

        self.bookings.append(booking)

        result = f"✓ Booking confirmed!\n\n"
        result += f"Confirmation Number: {booking['confirmation_number']}\n"
        result += f"Property: {booking['airbnb_name']}\n"
        result += f"Address: {booking['address']}\n"
        result += f"Guest: {booking['guest_name']}\n"
        result += f"Check-in: {booking['check_in']}\n"
        result += f"Check-out: {booking['check_out']}\n"
        result += f"Nightly Rate: ${booking['total_price']}\n\n"
        result += f"You'll receive a confirmation email shortly. Have a great stay!"

        return result        

async def entrypoint(ctx: agents.JobContext):
    """Entry point for the agent."""
    #try:
     #   logger.info("Starting agent initialization...")
        
        # ... your existing VAD, STT, LLM setup ...
        
        # Use the working TTS
      #  tts_instance = WorkingTTSFinal(
       #     sample_rate=24000,
        #    num_channels=1,
         #   voice="default"
        #)
        
        #logger.info("TTS initialized successfully")
        
        # ... rest of your VoiceAssistant setup ...
        
    #except Exception as e:
     #   logger.error(f"Failed to initialize agent: {e}")
      #  raise
    #tts_engine = RealtimeTTSNoPyAudio(
     #   voice="zira",  # Try "david" for male voice
      #  sample_rate=22050,
       # rate=220  # Slightly faster speech
    #)
    # Configure the voice pipeline with Bark TTS
    session = AgentSession(
        stt=deepgram.STT(model="nova-2"),
        llm=openai.LLM(model=os.getenv("LLM_CHOICE", "gpt-4o-mini")),
        #tts=openai.TTS(voice="echo"),
        
        tts=cartesia.TTS(
        model="sonic-3",
        voice="f786b574-daa5-4673-aa0c-cbe3e8534c02",
        ),
        
        #tts=rime.TTS(
        #model="mistv2",
        #speaker="rainforest",
        #speed_alpha=0.9,
        #reduce_latency=True,
        #),
        #tts=tts_instance,
        
        #tts=minimax.TTS(
        #),

        #tts=tts_engine,  # Real-time streaming TTS!

        # Use Bark TTS - Replace the previous TTS line with this:
        #tts=BarkTTSPlugin(
         #   device="auto",
          #  sample_rate=22050,
           # voice="v2/en_speaker_6",  # Default female voice
            #use_small_models=True,    # Faster loading
            #text_temp=0.7,
            #waveform_temp=0.7
        #),
        
        # In entrypoint function:
        #tts=CoquiTTSPlugin(
        #model_name="tts_models/en/ljspeech/tacotron2-DDC",  # Fast, good quality
        #device="auto",
        #sample_rate=22050
        #),

    # In entrypoint function:
        #tts=EdgeTTSPlugin(
        #voice="en-US-AriaNeural",  # Very natural female voice
        #rate="+10%",  # Slightly faster speech
        #pitch="+0Hz",
        #sample_rate=22050
        #),

        #tts=SuperFastCoquiTTSPlugin(sample_rate=22050),
        #tts=ReliableFastCoquiTTSPlugin(sample_rate=22050),

        #tts = KittenTTSPlugin(
        #model_name="kitten-tts-nano-0.1",  # You can change this model
        #voice="expr-voice-2-f",  # You can change this voice
        #sample_rate=24000),

        #tts=ctx.proc.userdata.get("tts") or ChatterboxTTSPlugin(
         #   device="cpu",  # Using CPU mode - change to "cuda" if GPU available
          #  #exaggeration=0.5,
           # #cfg_weight=0.5,
        #),

        #tts=ChatterboxTTSPlugin(
        #device="auto",
        #sample_rate=22050,
        #multilingual=False
        #),

        #tts=XTTSV2Plugin(
         #   device="auto",
          #  sample_rate=22050,
           # language="en",                    # Language
            #speaker_wav="my_voice.wav",       # Your voice sample (optional)
            #temperature=0.75,                 # Creativity (0.1-1.0)
            #length_penalty=1.0,               # Speech length control
            #repetition_penalty=5.0,           # Avoid repetition
            #top_k=50,                        # Diversity
            #top_p=0.85                       # Nucleus sampling
        #),

        #tts=silero.TTS(
         #   language="en",
         #   speaker="en_1",      # Female voice (try en_10, en_117 for other females)
         #   sample_rate=22050
        #),

        #tts = EdgeTTSPlugin(
         #   voice="en-US-AriaNeural",  # Female voice
          #  sample_rate=22050
        #),


        vad=silero.VAD.load(),
    )

    # Start the session
    await session.start(
        room=ctx.room,
        agent=Assistant()
    )

    # Generate initial greeting
    await session.generate_reply(
        instructions="Greet the user warmly and say: Hello, my name is Samantha, and I'm calling from ABC company. How are you doing today?”"
    )

if __name__ == "__main__":
    # Run the agent
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))