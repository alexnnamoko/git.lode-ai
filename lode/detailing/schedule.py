import math

def bar_area(diameter_mm):
    if diameter_mm<=0: raise ValueError('Bar diameter must be positive.')
    return math.pi*diameter_mm**2/4

def choose_bars(required_area_mm2, diameters=(10,12,16,20,25,32), min_bars=2, max_bars=12):
    if required_area_mm2<=0: raise ValueError('Required steel area must be positive.')
    choices=[]
    for d in diameters:
        n=max(min_bars,math.ceil(required_area_mm2/bar_area(d)))
        if n<=max_bars:
            provided=n*bar_area(d); choices.append({'bar_diameter_mm':d,'number_of_bars':n,'provided_area_mm2':provided,'excess_area_mm2':provided-required_area_mm2,'designation':f'{n}T{d}'})
    if not choices: raise ValueError('No bar arrangement in the supported range can provide the required area.')
    return min(choices,key=lambda x:(x['excess_area_mm2'],x['number_of_bars']))

def beam_schedule(required_area_mm2, link_diameter_mm=8, link_spacing_mm=None, cover_mm=None):
    bars=choose_bars(required_area_mm2)
    return {'member':'Preliminary beam reinforcement schedule','bottom_main_bars':bars['designation'],'bar_diameter_mm':bars['bar_diameter_mm'],'number_of_bars':bars['number_of_bars'],'As_required_mm2':required_area_mm2,'As_provided_mm2':bars['provided_area_mm2'],'links':f'2-leg T{link_diameter_mm} links' + (f' @ {link_spacing_mm} mm' if link_spacing_mm else ' — spacing NOT designed'),'cover_mm':cover_mm,'status':'PRELIMINARY — anchorage, laps, curtailment, support/top steel, spacing and full detailing checks are not generated.'}
