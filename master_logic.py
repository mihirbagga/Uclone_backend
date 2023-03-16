## Spliting name audio V1
from pydub import AudioSegment
from pydub.silence import split_on_silence
from pydub.effects import normalize, high_pass_filter
import moviepy.editor as mp
from PIL import Image, ImageDraw, ImageFont
import os
import vimeo
import base64
import smtplib
from email.mime.text import MIMEText
import gspread
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

##This will reside in env
sender_email = "rsudeep48@gmail.com"
sender_password = "csrxjcxirmznrcfd"

##Excel Creds
SHEET_ID = '1F8XPg9hoGb7Fa9yLMsYLk-mt1kibA_ygKgViyTBwSgs'
SHEET_NAME = 'Sheet1'
gc = gspread.service_account('token.json')
spreadsheet = gc.open_by_key(SHEET_ID)
worksheet = spreadsheet.worksheet(SHEET_NAME)

## This is final code
## Finalising this code
t_silent = 0.9 ## Starting of the video for which person is doing nothing
t_start = 1.9 ## Actual start of the video

def fetch_names_and_email():
    rows = worksheet.get_all_records()
    df = pd.DataFrame(rows)
    return df['FirstName'].values.tolist(), df['Email'].values.tolist()

def fetch_data():
    rows = worksheet.get_all_records()
    df = pd.DataFrame(rows)
    return df

def update_data(row_num,col,value):
    if col == 'VideoLink':
        col = 'C'
    if col == 'LandinPage':
        col = 'D'
    if col == 'EmailSent':
        col = 'E'
    worksheet.update(col+str(row_num), value)

# Open the two images
def create_thumbnail(name):
    ##This will reside in env
    template_image = Image.open('template.png')
    # Set up the variables
    name = name.upper()
    text = f"HI {name}"
    font_size = 150
    font = ImageFont.truetype('/Library/Fonts/Arial Bold.ttf', font_size)
    text_width, text_height = font.getsize(text)
    whatsapp_logo = Image.open('whatsapp_logo.png').convert('RGBA')
    whatsapp_logo_width, whatsapp_logo_height = whatsapp_logo.size

    # Resize the WhatsApp logo
    whatsapp_logo_ratio = whatsapp_logo_width / whatsapp_logo_height
    new_logo_height = int(text_height * 1.2)
    new_logo_width = int(new_logo_height * whatsapp_logo_ratio)
    whatsapp_logo_resized = whatsapp_logo.resize((new_logo_width, new_logo_height))

    # Calculate the size of the rectangle
    rectangle_width = text_width + new_logo_width + 30
    rectangle_height = max(text_height + 20, new_logo_height + 20)

    # Create the image and draw the rectangle
    # Specify the color of the rectangle in hex format
    rectangle_color = "#1a9e0f"
    image = Image.new('RGB', (rectangle_width, rectangle_height), color=rectangle_color)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, rectangle_width-1, rectangle_height-1), outline=rectangle_color)

    # Add the text
    text_x = 10
    text_y = (rectangle_height - text_height) // 2
    draw.text((text_x, text_y), text, fill='white', font=font)

    # Add the WhatsApp logo
    whatsapp_logo_x = text_width + 20
    whatsapp_logo_y = (rectangle_height - new_logo_height) // 2
    image.paste(whatsapp_logo_resized, (whatsapp_logo_x, whatsapp_logo_y), whatsapp_logo_resized)

    # Save the image
    image.save(f'green_banner/{name}.png', dpi=(1200,1200))

    
    name_image = Image.open(f'green_banner/{name}.png')

    # Calculate the location to paste Image B onto Image A
    y_location = (template_image.height - name_image.height) // 2
    x_location = int(0.8 * template_image.width) - name_image.width  # subtract 20% of Image B's width from the right edge of Image A
    location = (x_location, y_location)

    # Check if the location is valid
    if location[0] < 0 or location[1] < 0:
        print("Error: Image B is too large to fit onto Image A at the specified location.")
    else:
        # Paste Image B onto Image A
        template_image.paste(name_image, location)
        # Save the result
        template_image.save(f'static/{name}.png')

def split_audio(audio_filename):
    audio_file = AudioSegment.from_wav(f"uploads/audio/{audio_filename}.wav")
    silence_threshold = 500
    output_format = "wav"

    name_calls = split_on_silence(audio_file, min_silence_len=silence_threshold, silence_thresh=-40)

    for i, name_call in enumerate(name_calls):
        output_file = f"audio_clip/name_call_{i}.{output_format}"
        name_call.export(output_file, format=output_format)
        print(f"Saved {output_file}")
    
    # specify the directory path
    path = 'audio_clip'
    audio_files = []
    # iterate through the directory
    for filename in os.listdir(path):
        if filename.endswith('.wav'):
            audio_files.append(filename)
    audio_files = sorted(audio_files)
    return audio_files

def audio_mapper(audio_files):
    names_and_audios = []
    names = fetch_names_and_email()[0] #Need to fetch this from google sheets API
    audio_dir = "audio_clip"
    for name, audio_file in list(zip(names,audio_files)):
        audio_path = audio_dir + '/' + audio_file
        audio = mp.AudioFileClip(audio_path)
        names_and_audios.append((name,audio))
    return names_and_audios

def process_video(names_and_audios,video_filename):
    # Load the video file and audio file
    video = mp.VideoFileClip(f"uploads/video/{video_filename}.mov")
    for name,audio in names_and_audios:
        # Taking this part of the video to add audio
        clip = video.subclip(t_silent, t_start)

        rest_clip = video.subclip(t_start, video.duration)
        
        # loading audio file
        # audio = mp.AudioFileClip("audio_clip/name_call_5.wav") #.subclip(0, 1)

        audioclip = audio.subclip(0,audio.duration)

        # adding audio to the video clip
        videoclip = clip.set_audio(audioclip)

        # Clipping 
        final_video = mp.concatenate_videoclips([videoclip, rest_clip])
        
        full_file_address = "output_clips/" + name + ".mp4"
        final_video.write_videofile(full_file_address)

## Need to fetch from google sheets names
def upload_video(names_and_email):
    ## Upload video to vimeo Updates google sheet sends email to user
    ## This will be in env
    client = vimeo.VimeoClient(
        token='b5b5c3e495717422588a5125fdcd767c',
        key='2b09eee794e5d6671d8d14bb8c26d7b7d507e213',
        secret='gZVPTjaWor+rI3kMXbD031jJt6Hf1QbK0rJar9j6KutE64hAk0MX22j8zCl1+rUvDtjzBc3wYuwRsjd0AuQSg5j453fl1niIID/jG1pRcSs9LHvuySBqCzjR6Eaf7SDr'
    )
    ## Need to fetch from google sheets
    uris = []
    # Loop through the list of video names upload video and its thumbnail
    print("Uploading video to vimeo")

    for name, email in zip(names_and_email[0],names_and_email[1]):
        row_num = 2
        # Create the thumbnail
        create_thumbnail(name)
        # Open the thumbnail image and encode it as base64
        with open(f'static/{name}.png', 'rb') as thumb_file:
            encoded_thumb = base64.b64encode(thumb_file.read()).decode('utf-8')
        # Upload the video file
        file_name = 'output_clips/{}.mp4'.format(name)
        uri = client.upload(file_name, data={
            'name': 'Hi ' + name,
            'privacy': {
                'view': 'anybody'
            }
        })
        # Set the thumbnail for the video
        client.upload_picture(uri,f'static/{name}.png',activate=True)

        # Print the video URI
        uris.append(uri)

        video_url = "https://vimeo.com/manage"+uri
        update_data(col='VideoLink',row_num=row_num,value=video_url)
        update_data(col='LandinPage',row_num=row_num,value=f'http://127.0.0.1:5000/landing_page?name={name}&video_url={video_url}')

        #Emailing users
        print("Sending email")
        send_email(name=name,vimeo_url=video_url,recipient_email=email)
        print("email Sent sucessfully")
        update_data(col='EmailSent',row_num=row_num,value='Yes')

        print ('Your video URI is: %s' % (video_url))
        ## Add this URI to google sheets
        row_num = row_num + 1
    print("Video uploaded suceesfully")
    return uris

##name will be fetched from google sheets, with vimeo URL
def send_email(name,vimeo_url,recipient_email):
    subject = f"Hi {name}"
    body = f"""
    <html>

    <head>
    <meta http-equiv=Content-Type content="text/html; charset=utf-8">
    <meta name=Generator content="Microsoft Word 15 (filtered)">

    </head>

    <body lang=EN-US link=blue vlink="#954F72" style='word-wrap:break-word'>

    <div class=WordSection1>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>Hi {name},</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>My name's Jonny, it's great to connect with
    you and&nbsp;I&nbsp;really enjoyed preparing your invitation.&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='margin-bottom:12.0pt;background:white'><span
    lang=EN-IN style='font-family:"Arial",sans-serif;color:#222222'>I&nbsp;made
    this&nbsp;</span><span lang=EN-IN style='color:black'><a
    href={vimeo_url} target="_blank"><b><span
    style='font-family:"Arial",sans-serif;color:#1155CC'>personal&nbsp;video</span></b></a></span><b><span
    lang=EN-IN style='font-family:"Arial",sans-serif;color:#222222'>&nbsp;</span></b><span
    lang=EN-IN style='font-family:"Arial",sans-serif;color:#222222'>for you
    because&nbsp;I&nbsp;believe first impressions matter.&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='color:black'><a
    href="{vimeo_url}" target="_blank"><span
    style='font-family:"Arial",sans-serif;color:#1155CC;text-decoration:none'><img
    border=0 width=602 height=371 id="Picture 8"
    src="https://ci6.googleusercontent.com/proxy/CJQoi0hs9ILjSZfeUTPrGUe66bnt60GPI7n9WNM7RLrVacgzHgfcsnXvJlj0GX92uEKtZ9SXEs-5X5iZeDBcK1gU8958gO6B_e_oeOD3uIXLQ-vq3CNG3-ABEW5uiBZ-3EDNET8A-BUWW1Z73FMoJ2bRX4HJnNzWohFXoRM3y1Htd8pegqbd6WXM2R-WFbr_9-Eip6v_cLbCWtns0Ocjjlh-wR8I9BQ=s0-d-e1-ft#https://p-ngfkgm.t2.n0.cdn.getcloudapp.com/items/Z4unzkpG/94d484c8-c037-4554-b6f6-0788efc27ba1.jpg?source=viewer&v=dd3e48159afb17b350c60bce52c86b22"
    alt="Graphical user interface, diagram&#10;&#10;Description automatically generated"></span></a></span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>You might be wondering why I’m reaching
    out?&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>It's because&nbsp;we're offering the
    opportunity for a few pre-selected&nbsp;entrepreneurs, consultants, coaches to
    join&nbsp;me in a&nbsp;<b>complimentary&nbsp;Private 1-1 WhatsApp
    Conversation&nbsp;</b>where&nbsp;I'm sharing what&nbsp;I've discovered from a
    series of experiments that has allowed me to generate&nbsp;<b>+/$551,352.97
    USD&nbsp;<u>net</u></b>&nbsp;in extra net cash for my business.&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><b><span lang=EN-IN
    style='font-family:"Arial",sans-serif;color:#222222'>By leveraging&nbsp;a brand
    new automated organic client generating machine using Open AI + ChatGPT +
    WhatsApp&nbsp;that creates massive attention&nbsp;<u>for free.</u>&nbsp;&nbsp;</span></b></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>I believe we'll take this to $930,000 usd in
    the next 3-5 months.&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>Frankly the results have been astonishing.</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>I&nbsp;find it hard to believe myself but you
    can&nbsp;</span><span lang=EN-IN style='color:black'><a
    href="http://127.0.0.1:5000/landing_page?name={name}&video_url={vimeo_url}"
    target="_blank"><b><span style='font-family:"Arial",sans-serif;color:#1155CC'>read
    more about it with specifics proof here</span></b></a></span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'><img border=0 width=602 height=354
    id="Picture 7" src="https://ci3.googleusercontent.com/proxy/5uDM_HBo-TBCwKPO_i3UFQRIGftJSyZ3Ixn7VF5by4fAAXep9s8jAJoJCeEV8dse5J-xdjhocgEo9BmKfrsntr-4ZPw6BIvGqX0CKSGnu3NesWfZLAc-GRKBGuIlYe0puvAEKzuA2GnualE8JgdxuA783AFzmpCUvmQ-T_CEBJj7bAVQpUHuMFuNvcj11Vl03rN7bEaHqCYkHXA386pG42tAOQTC7jI=s0-d-e1-ft#https://p-ngfkgm.t2.n0.cdn.getcloudapp.com/items/rRugXKL4/060b3c44-7e41-48dc-a737-e1712793013f.jpg?source=viewer&v=fbc39bc40901e4aa1594ebbeb69b739c"></span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><b><span lang=EN-IN
    style='font-family:"Arial",sans-serif;color:#222222'>Most people think there is
    something wrong with them about why their business isn't making the&nbsp;amount
    of money it&nbsp;should be, but in actuality it’s because&nbsp;obscurity is the
    real reason why almost all businesses fail.</span></b><span lang=EN-IN
    style='font-family:"Arial",sans-serif;color:#222222'><br>
    <br>
    <u>No one knows who they are</u>.&nbsp;<br>
    <br>
    <br>
    </span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>If you're not hitting +20k
    minimum&nbsp;months, it’s simply because not enough people know about
    you.&nbsp;It's not your fault, how could it be?</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'><br>
    Because you don't yet have a simple, powerful and free way of&nbsp;<b><u>scaling
    your attention for free.</u></b></span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'><img border=0 width=602 height=439
    id="Picture 6" src="https://ci5.googleusercontent.com/proxy/A4hJCAdX2Mm2FVERW8hpr_ay2nKdc1HSTZeflse7EmanE-B5Lwp_rCMSXsR26IjoS_-Lt4CBkT6_bfM82dkwhGrgEg6XwglXO6R4BXdKQWUYQsaeGvD7rLIxlJNQCP1Of_0Abhu7toFWs9fPCdQ8-wvVvE9PDYEAF2q1QIleGfHJk60zKKoQXD9ilyevpL_irXEz6b-eAvxzNdA7OaOI4Jd371lSQ7Q=s0-d-e1-ft#https://p-ngfkgm.t2.n0.cdn.getcloudapp.com/items/L1u6mAxp/6a4552e5-bfbe-4a47-bcdf-04d3d8c70317.jpg?source=viewer&v=0bd3c3023667dca3ae94edfe36f5f9c2"></span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'><br>
    <b>It's become the single most important success factor today in 2023 to&nbsp;<u>generate
    attention for free</u>, rather than spending money to acquire attention
    (expensive paid ads and alike).&nbsp;</b></span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>If you're struggling to generate high quality
    lead flow in 2023, it's because you're still painfully thinking and/or doing&nbsp;<u>the
    old way&nbsp;and not leveraging the&nbsp;new way</u><b>,&nbsp;</b>now made
    possible with powerful&nbsp;<b>brand new AI technology to&nbsp;<u>generate
    attention for free</u>.&nbsp;</b><br>
    <br>
    Combined with the correct&nbsp;<b>First Principle System to&nbsp;<u>scale that
    free attention indefinitely.</u>&nbsp;</b><br>
    <br>
    So you can&nbsp;scale your freedom&nbsp;and&nbsp;build a war chest of net cash
    at all times.</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>Because anything else is just&nbsp;expensive,
    wasteful, and nonsense.&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>It's&nbsp;<b><u>no longer required</u></b>&nbsp;when
    leveraging this new era of powerful&nbsp;<b>First Principle AI Systems.&nbsp;</b></span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'><br>
    <img border=0 width=487 height=466 id="Picture 5"
    src="https://ci3.googleusercontent.com/proxy/FEq-gDhGsFcrCT42a0Qh6ytEA6lapeIuSknlFEyOiMSU_qMbMMa7ymPi9tctgegef8Tpp0Ex_9TAImw0GbFhsE5SFUzbVNqQow9vwvVKPIYhpeBP96YBj7Ztw3jXcI5NMFruIreWqmqQF7zNBGFTKVmluwB44mOQH7gcaqu7DTlImrYvjhtmCPuCVFKmpmecbeIU4Kf1hLW_FBfmLfyxFvoNU5dCHVg=s0-d-e1-ft#https://p-ngfkgm.t2.n0.cdn.getcloudapp.com/items/4guNYlGv/418743a4-2278-4f75-aa7e-9dbaf64a4254.jpg?source=viewer&v=8453fb29f8c506041022c1cfd32d5c83"></span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>My goal is to help the right type of
    entrepreneurs who either have an existing business or a civilian looking to
    start a brand new business to&nbsp;<u>make money without having to invest a lot
    of money.</u></span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>Because&nbsp;you're now&nbsp;leveraging
    powerful brand new&nbsp;<b>AI technologies</b>&nbsp;+&nbsp;embedding a simple
    hands off&nbsp;<b>First Principle System</b>&nbsp;that works for you on autopilot.&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><b><span lang=EN-IN
    style='font-family:"Arial",sans-serif;color:#222222'>An automated organic
    client generating machine using Open AI, ChatGPT &amp; WhatsApp&nbsp;that
    creates massive attention&nbsp;<u>for free at scale:</u></span></b></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><b><span lang=EN-IN
    style='font-family:"Arial",sans-serif;color:black'>Without expensive paid ads </span></b></p>

    <p class=MsoNormal style='background:white'><b><span lang=EN-IN
    style='font-family:"Arial",sans-serif;color:black'>Without complicated funnels<br>
    <br>
    </span></b></p>

    <p class=MsoNormal style='background:white'><b><span lang=EN-IN
    style='font-family:"Arial",sans-serif;color:black'>Without time sucking sales
    calls</span></b></p>

    <p class=MsoNormal style='background:white'><b><span lang=EN-IN
    style='font-family:"Arial",sans-serif;color:black'><br>
    <br>
    </span></b></p>

    <p class=MsoNormal style='background:white'><b><span lang=EN-IN
    style='font-family:"Arial",sans-serif;color:black'><img border=0 width=600
    height=197 id="Picture 4" src="https://ci4.googleusercontent.com/proxy/FGvhKK059A1Tot-gjLoPBN2eWzhAd-C5ls6imA-7n-prTofoMMPx-DSIZCx-4ijJX5PgabgFVZcc6aYSPAW6nHKG7xiwZT8UPCNZ0qN59I-TNWu_LT6cuGOW-Q1koNJ0YvJXHnVuxmJGPrN4F3WwMQ39sM80ZMtBujJ2cgWGoyiZAdtSS0M7VsV9dfyAPuExM-HH1jemADX5o9bBCAMpju09OhqWB0Q=s0-d-e1-ft#https://p-ngfkgm.t2.n0.cdn.getcloudapp.com/items/Qwu86lpy/326ad677-5c7f-4339-b596-33b31c40fbbc.jpg?source=viewer&v=5e34550e3f8a5f06598326c34f7550ff"
    alt="Graphical user interface, text, application&#10;&#10;Description automatically generated"></span></b><b><span
    lang=EN-IN style='font-family:"Arial",sans-serif;color:black'><br>
    <br>
    </span></b></p>

    <p class=MsoNormal style='background:white'><b><span lang=EN-IN
    style='font-family:"Arial",sans-serif;color:black'><br>
    <br>
    </span></b></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>So what are the next steps?&nbsp;</span><b><span
    lang=EN-IN style='font-family:"Arial",sans-serif;color:black'> </span></b></p>

    <p class=MsoNormal style='background:white'><b><span lang=EN-IN
    style='font-family:"Arial",sans-serif;color:#222222'>Step 1:&nbsp;</span></b><span
    lang=EN-IN style='font-family:"Arial",sans-serif;color:#222222'>If you're new
    to WhatsApp as an application, it's very simple and you can download it&nbsp;</span><span
    lang=EN-IN style='color:black'><a
    href="http://ec2-52-26-194-35.us-west-2.compute.amazonaws.com/x/d?c=13944033&amp;l=cd43c779-d617-4bfb-8743-512cca40a03d&amp;r=a34864a4-a987-4fda-a0a4-9de1a018c5e2"
    target="_blank"><b><span style='font-family:"Arial",sans-serif;color:#1155CC'>here</span></b></a></span><b><span
    lang=EN-IN style='font-family:"Arial",sans-serif;color:#222222'>.</span></b><span
    lang=EN-IN style='font-family:"Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>Once it's downloaded use your invitation link
    below to the&nbsp;<b>Complimentary&nbsp;Private 1-1 WhatsApp Conversation.</b></span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>Here's your RSVP link:&nbsp;</span><span
    lang=EN-IN style='color:black'><a href="https://wa.me/447729296227"
    target="_blank"><b><span style='font-family:"Arial",sans-serif;color:#1155CC'>{name}'s
    Invitation</span></b></a></span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='color:black'><a
    href="https://wa.me/447729296227" target="_blank"><span style='font-family:
    "Arial",sans-serif;color:#1155CC;text-decoration:none'><img border=0 width=420
    height=408 id="Picture 3" src="https://ci4.googleusercontent.com/proxy/H0bw428u1V57ZLtu3_8GupIey7mIwTnBITw31wZq6OQqtupmjzZE8cad6MktoeaeZPcEqC-A3vxs1OrNBYKCOV0c9I_rwUjPsQxQwP7MrxE7veM_qaG8-PA0SovzgDTZQR4Sb5xn-7OZ_jcsT_xKLMjqclWjO24js0uay_4VM0qQuZqA2nq1fOlz_hzvWmN5MkZwg4Hw3k9kFpKL_s3oCqsgAWSq3xc=s0-d-e1-ft#https://p-ngfkgm.t2.n0.cdn.getcloudapp.com/items/eDunqOoK/87d40c13-3151-461f-879d-27888509fa34.jpg?source=viewer&v=9667f9ea46367eab612f53eac5e3b45b"></span></a></span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><b><span lang=EN-IN
    style='font-family:"Arial",sans-serif;color:#222222'>Step 2:&nbsp;</span></b><span
    lang=EN-IN style='font-family:"Arial",sans-serif;color:#222222'>When you arrive
    into the&nbsp;<b>Complimentary&nbsp;Private 1-1 WhatsApp Conversation</b>&nbsp;with
    me please&nbsp;<u>introduce yourself</u>&nbsp;with the following so that I can
    welcome you properly.&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>- Full Name</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>- Your Niche&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>- Purpose&nbsp;Behind Your Business&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>- Your Current &amp; Desired Situation&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>- Where You'd Like To Be 12 Months From Now<br>
    - Your Current Business Monthly Revenue&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>- How your currently generating leads and
    making sales</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><b><span lang=EN-IN
    style='font-family:"Arial",sans-serif;color:#222222'>Access to
    this&nbsp;Private 1-1 WhatsApp Conversation, all the coaching that comes with
    it and platform access via our brand new Private AI Bullets Vault, where I'll
    be demonstrating this brand new AI system, will be&nbsp;<u>free of charge</u></span></b></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>However, your private invitation link
    will&nbsp;<b>only be available for</b>&nbsp;<b>the next 24hrs&nbsp;</b>only
    before&nbsp;I&nbsp;manually reset the link and we move to the next on our list
    of invites.&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>Specifically&nbsp;you won’t get a response
    should you miss this 24hr deadline&nbsp;because the opportunity is a&nbsp;first
    come first served basis&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>We're capping the number of conversations to
    maintain quality and exceed the experience and expectations for each of our
    complimentary guests during our time together.<br>
    <br>
    So if you're curious, but also serious you'll want to ensure you join the chat
    in the next 24hrs or less.&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='margin-bottom:12.0pt;background:white'><span
    lang=EN-IN style='font-family:"Arial",sans-serif;color:#222222'><img border=0
    width=447 height=852 id="Picture 2" src="https://ci5.googleusercontent.com/proxy/lg2nwJWPInagDLUkeR4Svxvvx2eN7PaRuzLSdJlH-lE0wkJMvz54FK6uWUvn5nO3j-yVLuP830WmhVRsDEXaPYzOPFwWOiP83VOaNne68yJzUX8pJuwJoYlkGPhjQbhxtSDN-R9U6Of2Bk9MrKWiY-o1du59TXzBNtTDfQPK-LnN9WyiTctNDGXugh89k4FZGUPVKrR1jCsEA1Ahn6amVhQ7BbObulc=s0-d-e1-ft#https://p-ngfkgm.t2.n0.cdn.getcloudapp.com/items/7Kuzxbly/17faa859-7924-41ad-9874-0ad7392d876c.jpg?source=viewer&v=3b8cc566a581322245a97ecac10dfff9"></span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>If I don't instantly respond upon you
    entering our&nbsp;<b>Private 1-1 WhatsApp Conversation&nbsp;</b>nothing is
    wrong.</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'><br>
    I'm simply at my desk working or asleep based on my timezone (I'm based in
    Dubai) and because I have manners I like to welcome every single guest&nbsp;<b><u>personally</u></b>.&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'><br>
    Please be patient, and ensure you have messaged me first with the above
    introduction exactly, otherwise I won't know you've arrived at the start of our
    conversation together to provide you with the important next steps.&nbsp;&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'><br>
    This&nbsp;opportunity is for those who have<b>&nbsp;etiquette and
    manners,&nbsp;</b>and for&nbsp;those who are&nbsp;<b>curious,&nbsp;open minded
    and respectful.&nbsp;</b></span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'><br>
    See you on the other side {name}.<br>
    <br>
    Thanks,<br>
    Jonny</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>&nbsp;</span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'>P.S. I'm a real&nbsp;person. Here's my&nbsp;</span><span
    lang=EN-IN style='color:black'><a
    href="http://ec2-52-26-194-35.us-west-2.compute.amazonaws.com/x/d?c=13944033&amp;l=a9e11892-3844-4ae2-8047-4a8fc03c3549&amp;r=a34864a4-a987-4fda-a0a4-9de1a018c5e2"
    target="_blank"><b><span style='font-family:"Arial",sans-serif;color:#1155CC'>Instagram</span></b></a></span></p>

    <p class=MsoNormal style='background:white'><span lang=EN-IN style='font-family:
    "Arial",sans-serif;color:#222222'><img border=0 width=240 height=251
    id="Picture 1" src="https://ci3.googleusercontent.com/proxy/bNWrdBS0D0u4jUR9RTK-t3RgWotOpj08su6zl6h8NrEjnxImn6e4ZbrHyNgAzv2Tot5qwe7flYsFq1pWtvDZpLTC41shIFn3iRogauPwH6OasDcU8kOzlrOmC9y4uJpt96JHBs_4ZKjL2tsNL1JFLx-hdVGe_NvPBikCnavXRl9mOIy4LCe6BlDKJjeo05x89Xs6DOPq5aIRlwWK227qM4wVe-HMhPKESJM=s0-d-e1-ft#https://p-ngfkgm.t2.n0.cdn.getcloudapp.com/items/qGuvLvxJ/Image%202020-11-09%20at%2010.09.25%20am.png?source=viewer&v=5ffefc8bcdf8a56735a43a05f97e3229"></span></p>

    <p class=MsoNormal><span lang=EN-IN>&nbsp;</span></p>

    </div>

    </body>

    </html>


    """
    html_message = MIMEText(body, 'html')
    html_message['Subject'] = subject
    html_message['From'] = sender_email
    html_message['To'] = recipient_email

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, recipient_email, html_message.as_string())
    server.quit()


