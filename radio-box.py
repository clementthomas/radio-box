# -*- coding: utf-8 -*
import vlc
import time, sched
from gpiozero import LED, Button, DigitalOutputDevice
from signal import pause
from datetime import datetime
from grove_rgb_lcd import *
import os,signal,sys
from vlc import EventType
import random
import pdb
import threading

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
        ('Radio Sympa','http://radio2.pro-fhi.net:9095/stream2'),
        ('mega','http://live.francra.org:8000/Radio-Mega'),
        ('France Inter','http://direct.franceinter.fr/live/franceinter-midfi.mp3'),
        ('FIP','http://direct.fipradio.fr/live/fipnantes-midfi.mp3'),
        ('France culture','http://direct.franceculture.fr/live/franceculture-midfi.mp3'),
        ('St Fereol','http://live.francra.org:8000/RadioSaintFerreol.m3u'),
	('Grenouille','http://live.radiogrenouille.com/live.m3u'),
    ],
    'current_station':0,
    'current_lcd_text':'',
    'state':'stopped' #stopped, loading, playing
}

def main():
    #set volume to vlc
    context['playerList'].get_media_player().audio_set_volume(60)

    #Set handler when station reached
    context['playerList'].get_media_player().event_manager().event_attach(EventType.MediaPlayerPlaying, stationReached)

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
        context['state'] = 'stopped'
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

def print_lcd(text, no_refresh=False):
    '''
        display on LCD
    '''
    try:
        if no_refresh:
            setText_norefresh(text)
        else:
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
    context['state'] = 'loading'

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

    playerList.set_media_list(mediaList)
    playerList.play()


def stationReached(event):
    '''
        callback of MediaPlayerList when playing
    '''
    context['state'] = 'playing'
    context['title_position'] = 0
    station_id = context.get('current_station')
    station = context.get('stations')[station_id]
    print('Station Reached !')
    print_lcd('%s !'%(station[0],))
    displayTitle()

def getTitle():
    station_id = context.get('current_station')
    station = context.get('stations')[station_id]
    media = context.get('playerList').get_media_player().get_media()
    title = media.get_meta(12)
    if not title:
        title = ''
    return title

def displayTitle():
    title = getTitle()
    print('len : %s'%(len(title),))
    if len(title) <= 16:
        print_lcd('\n%s'%(title.ljust(16),), no_refresh=True)
    else:
        #Update title every 0.5 second
        threading.Timer(0.5, updateTitle, (0,)).start()


def updateTitle(position=0, old_title=None):
    if context['state'] == 'playing':
        title = None
        if position == -1:
            print_lcd('\n                ', no_refresh=True)
        elif position > -1:
            title = getTitle()
            title_mini = title[position:position+16]
            #if title change or scroll at the end of title : reset position
            if (old_title and old_title != title) or \
                (position + 16 == len(title)):
                position = -3
            print_lcd('\n%s'%(title_mini,), no_refresh=True)
        threading.Timer(0.5, updateTitle, (position+1,title)).start()

if __name__ == "__main__":
    main()
