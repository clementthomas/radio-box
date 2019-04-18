# -*- coding: utf-8 -*
import vlc
import time
from gpiozero import LED, Button, DigitalOutputDevice
from signal import pause
from datetime import datetime
from grove_rgb_lcd import *
import os,signal,sys
from vlc import EventType
import random
import pdb

#inputs
button1 = Button(26, bounce_time=0.2)
button2 = Button(13, bounce_time=0.2)
button3 = Button(16, bounce_time=0.2)
button4 = Button(5, bounce_time=0.2)
button5 = Button(6, bounce_time=0.2)
buttonOnOff = Button(25, hold_time=5)

#outputs
led = LED(24)
display = DigitalOutputDevice(23)

#funny sentences to say hello and good bye
hellos = ['Coucou !', 'Salut a toi !', 'Toujours en vie ?', 'Comment vas-tu ?', 'Besoin de rien\nEnvie de toi...', 'BlBblblBLbblb !!', 'Pourquoi pas ?', 'Salamalekoum', ':-)']
byes = ['Tchao l\'ami', 'Hasta la vista,\nBaby !', 'Hasta la victoria !', 'A plus \ndans l\'bus !', 'Bisous !']


context = {
    'playerList':vlc.MediaListPlayer(),
    'stations': [
	('Sing Sing','http://stream.sing-sing-bis.org:8000/singsingaac256'),
        ('Grenouille','http://live.radiogrenouille.com/live.m3u'),
        ('mega','http://live.francra.org:8000/Radio-Mega'),
        ('France Inter','http://direct.franceinter.fr/live/franceinter-midfi.mp3'),
        ('FIP Nantes','http://direct.fipradio.fr/live/fipnantes-midfi.mp3'),
        ('France culture','http://direct.franceculture.fr/live/franceculture-midfi.mp3'),
        ('St Fereol','http://live.francra.org:8000/RadioSaintFerreol.m3u'),
    ],
    'current_station':0,
    'current_lcd_text':'',
}

def main():
    #set function called when process stopped
    signal.signal(signal.SIGTERM, on_exit)
    
    #sequence to say hello 
    launch()
        
    #set button handlers
    buttonOnOff.when_held = shutdown #held after 5 seconds
    buttonOnOff.when_pressed = buttonOnOffPressed
    button1.when_pressed = buttonPressed
    button2.when_pressed = buttonPressed
    button3.when_pressed = buttonPressed
    button4.when_pressed = buttonPressed
    button5.when_pressed = buttonPressed
    
    #wait
    pause()

def launch():
    '''
        simple initializing sequence
    '''
    display.off()
    led.on()

def launch_funny():
    """
        funny and useless initializing sequence
    """
    display.on()
    print_lcd("Chargement...")
    
    time.sleep(1)
    
    for i in range(3):
        print_lcd(str(3-i)+'...')
        led.on()
        time.sleep(0.2)
        led.off()
        time.sleep(1)
      
    led.off()
    display.on()
    play(0)


def shutdown():
    '''
        shutdown raspbian        
    '''
    on_exit()
    os.system('sudo halt')
    
def buttonOnOffPressed():
    '''
        depending on display state.
        If display is on, switch the system off
        If display is off, switch the system on.
    '''
    if display.value:
        context.get('playerList').stop()
        print_lcd("%s"%(random.choice(byes),))
        time.sleep(1)
        print_lcd("")
        display.off()
        led.on()
    else:
        display.on()
        led.off()
        print_lcd("%s"%(random.choice(hellos),))
        time.sleep(1)        
        play()

def buttonPressed():
    '''
        handler when station button pressed
    '''
    
    
    #useless love code        
    if button1.is_pressed and button5.is_pressed:
        context['love'] = True
        context.get('playerList').get_media_player().event_manager().event_detach(EventType.MediaPlayerPlaying)
        print_lcd("Je t'aime")        
        return
    if context.get('love'):
        context['love'] = False
        context.get('playerList').get_media_player().event_manager().event_attach(EventType.MediaPlayerPlaying, stationReached, context['stations'][context['current_station']])
    #end of love code
    
    if button1.is_pressed:
        play(0)
    elif button2.is_pressed:
        play(1)
    elif button3.is_pressed:
        play(2)
    elif button4.is_pressed:
        play(3)
    elif button5.is_pressed:
        play(4)
    
    
def on_exit(sig=None, func=None):
    '''
        when process is stopped
    '''
    print_lcd("Adios !")
    time.sleep(1)
    print_lcd("")
    context.get('playerList').stop()
    sys.exit(1)

def print_lcd(text):
    '''
        display on LCD
    '''
    try:
        setText(text)
        context['current_lcd_text'] = text
    except OSError as e:
        try:
            setText(text) #try 2 time
        except OSError as e:        
            print('OS Error : %s (text = %s)'%(str(e),text))
    
        
def play(station_id=-1):
    '''
        play a station and display it on LCD followed by '...'
    '''
    playerList = context.get('playerList')
    if station_id == -1:
        station_id = context.get('current_station')
    else:
        context['current_station'] = station_id
        
    station = context.get('stations')[station_id]
    
    if playerList.is_playing():
        playerList.stop()
        
    print_lcd('%s...'%(station[0],))
    
    if 'm3u' in station[1]:
        mediaList = vlc.MediaList([station[1]])
        print('MediaPlayerList')
    else:
        mediaList = vlc.MediaList()
        mediaList.add_media(station[1])        
        print('MediaPlayer')
        
    playerList.get_media_player().event_manager().event_detach(EventType.MediaPlayerPlaying)
    playerList.get_media_player().event_manager().event_attach(EventType.MediaPlayerPlaying, stationReached, station)
        
    playerList.set_media_list(mediaList)    
    playerList.play()
    

def stationReached(event, station):
    '''
        callback of MediaPlayerList when playing
    '''
    print_lcd('%s !'%(station[0],))
   

if __name__ == "__main__":
    main()
