"""Football/Soccer Team Name Mapping"""

import re

FOOTBALL_TEAM_LOGOS = {
    # Premier League
    'ARS': 'https://resources.premierleague.com/premierleague/badges/t3.svg',
    'AVL': 'https://resources.premierleague.com/premierleague/badges/t7.svg',
    'BOU': 'https://resources.premierleague.com/premierleague/badges/t91.svg',
    'BRE': 'https://resources.premierleague.com/premierleague/badges/t94.svg',
    'BHA': 'https://resources.premierleague.com/premierleague/badges/t36.svg',
    'CHE': 'https://resources.premierleague.com/premierleague/badges/t8.svg',
    'CRY': 'https://resources.premierleague.com/premierleague/badges/t31.svg',
    'EVE': 'https://resources.premierleague.com/premierleague/badges/t11.svg',
    'FUL': 'https://resources.premierleague.com/premierleague/badges/t54.svg',
    'IPS': 'https://resources.premierleague.com/premierleague/badges/t40.svg',
    'LEI': 'https://resources.premierleague.com/premierleague/badges/t13.svg',
    'LIV': 'https://resources.premierleague.com/premierleague/badges/t14.svg',
    'MCI': 'https://resources.premierleague.com/premierleague/badges/t43.svg',
    'MUN': 'https://resources.premierleague.com/premierleague/badges/t1.svg',
    'NEW': 'https://resources.premierleague.com/premierleague/badges/t4.svg',
    'NFO': 'https://resources.premierleague.com/premierleague/badges/t17.svg',
    'SOU': 'https://resources.premierleague.com/premierleague/badges/t20.svg',
    'TOT': 'https://resources.premierleague.com/premierleague/badges/t6.svg',
    'WHU': 'https://resources.premierleague.com/premierleague/badges/t21.svg',
    'WOL': 'https://resources.premierleague.com/premierleague/badges/t39.svg',
    # Championship / Other (Adding placeholders)
    'LEE': 'https://resources.premierleague.com/premierleague/badges/t2.svg',
    'BUR': 'https://resources.premierleague.com/premierleague/badges/t90.svg',
    'SUN': 'https://resources.premierleague.com/premierleague/badges/t56.svg',
    'SHU': 'https://resources.premierleague.com/premierleague/badges/t49.svg',
    'LUT': 'https://resources.premierleague.com/premierleague/badges/t102.svg',
    'NOR': 'https://resources.premierleague.com/premierleague/badges/t45.svg',
    'WAT': 'https://resources.premierleague.com/premierleague/badges/t57.svg',
    'WBA': 'https://resources.premierleague.com/premierleague/badges/t35.svg',
}

FOOTBALL_TEAMS = {
    # Premier League
    'ARS': ('Arsenal', 'Arsenal', 'Arsenal'),
    'AVL': ('Aston Villa', 'Aston Villa', 'Aston Villa'),
    'BOU': ('Bournemouth', 'Bournemouth', 'AFC Bournemouth'),
    'BRE': ('Brentford', 'Brentford', 'Brentford'),
    'BHA': ('Brighton', 'Brighton', 'Brighton & Hove Albion'),
    'CHE': ('Chelsea', 'Chelsea', 'Chelsea'),
    'CRY': ('Crystal Palace', 'Crystal Palace', 'Crystal Palace'),
    'EVE': ('Everton', 'Everton', 'Everton'),
    'FUL': ('Fulham', 'Fulham', 'Fulham'),
    'IPS': ('Ipswich', 'Ipswich', 'Ipswich Town'),
    'LEI': ('Leicester', 'Leicester', 'Leicester City'),
    'LIV': ('Liverpool', 'Liverpool', 'Liverpool'),
    'MCI': ('Man City', 'Man City', 'Manchester City'),
    'MUN': ('Man United', 'Man United', 'Manchester United'),
    'NEW': ('Newcastle', 'Newcastle', 'Newcastle United'),
    'NFO': ('Nottingham Forest', 'Nottingham', 'Nottingham Forest'),
    'SOU': ('Southampton', 'Southampton', 'Southampton'),
    'TOT': ('Tottenham', 'Tottenham', 'Tottenham Hotspur'),
    'WHU': ('West Ham', 'West Ham', 'West Ham United'),
    'WOL': ('Wolves', 'Wolves', 'Wolverhampton Wanderers'),
    
    # Championship / Other
    'LEE': ('Leeds United', 'Leeds', 'Leeds United'),
    'BUR': ('Burnley', 'Burnley', 'Burnley FC'),
    'SUN': ('Sunderland', 'Sunderland', 'Sunderland AFC'),
    'SHU': ('Sheffield United', 'Sheffield Utd', 'Sheffield United'),
    'LUT': ('Luton', 'Luton', 'Luton Town'),
    'NOR': ('Norwich', 'Norwich', 'Norwich City'),
    'WAT': ('Watford', 'Watford', 'Watford FC'),
    'WBA': ('West Brom', 'West Brom', 'West Bromwich Albion'),
    
    # La Liga teams
    'BAR': ('Barcelona', 'Barcelona', 'FC Barcelona'),
    'RMA': ('Real Madrid', 'Real Madrid', 'Real Madrid'),
    'ATM': ('Atletico Madrid', 'Atletico', 'Atlético Madrid'),
    'SEV': ('Sevilla', 'Sevilla', 'Sevilla FC'),
    'VAL': ('Valencia', 'Valencia', 'Valencia CF'),
    'VIL': ('Villarreal', 'Villarreal', 'Villarreal CF'),
    'RSO': ('Real Sociedad', 'Sociedad', 'Real Sociedad'),
    'BET': ('Real Betis', 'Betis', 'Real Betis'),
    'GIR': ('Girona', 'Girona', 'Girona FC'),
    'ATH': ('Athletic Club', 'Athletic Club', 'Athletic Club'),
    
    # Bundesliga teams
    'BAY': ('Bayern Munich', 'Bayern', 'FC Bayern München'),
    'DOR': ('Dortmund', 'Dortmund', 'Borussia Dortmund'),
    'RBL': ('RB Leipzig', 'Leipzig', 'RB Leipzig'),
    'LEV': ('Leverkusen', 'Leverkusen', 'Bayer Leverkusen'),
    'STU': ('Stuttgart', 'Stuttgart', 'VfB Stuttgart'),
    
    # Serie A teams
    'JUV': ('Juventus', 'Juventus', 'Juventus'),
    'INT': ('Inter Milan', 'Inter', 'Inter Milan'),
    'MIL': ('AC Milan', 'AC Milan', 'AC Milan'),
    'NAP': ('Napoli', 'Napoli', 'SSC Napoli'),
    'ROM': ('Roma', 'Roma', 'AS Roma'),
    'LAZ': ('Lazio', 'Lazio', 'SS Lazio'),
    'ATA': ('Atalanta', 'Atalanta', 'Atalanta BC'),
    'FIO': ('Fiorentina', 'Fiorentina', 'ACF Fiorentina'),
    
    # Ligue 1 teams
    'PSG': ('PSG', 'PSG', 'Paris Saint-Germain'),
    'MAR': ('Marseille', 'Marseille', 'Olympique Marseille'),
    'LYO': ('Lyon', 'Lyon', 'Olympique Lyonnais'),
    'MON': ('Monaco', 'Monaco', 'AS Monaco'),
    'LIL': ('Lille', 'Lille', 'LOSC Lille'),
}

POLYMARKET_TO_CODE = {v[0]: k for k, v in FOOTBALL_TEAMS.items()}
KALSHI_TO_CODE = {v[1]: k for k, v in FOOTBALL_TEAMS.items()}
FULLNAME_TO_CODE = {v[2]: k for k, v in FOOTBALL_TEAMS.items()}

# Add common variations
POLYMARKET_TO_CODE['Manchester City'] = 'MCI'
POLYMARKET_TO_CODE['Manchester United'] = 'MUN'
POLYMARKET_TO_CODE['Brighton & Hove Albion'] = 'BHA'
POLYMARKET_TO_CODE['Nottingham'] = 'NFO'
POLYMARKET_TO_CODE['West Ham United'] = 'WHU'
POLYMARKET_TO_CODE['Wolverhampton'] = 'WOL'
POLYMARKET_TO_CODE['Atletico'] = 'ATM'
POLYMARKET_TO_CODE['Atlético Madrid'] = 'ATM'
POLYMARKET_TO_CODE['Real Sociedad'] = 'RSO'
POLYMARKET_TO_CODE['Real Betis'] = 'BET'
POLYMARKET_TO_CODE['Bayern'] = 'BAY'
POLYMARKET_TO_CODE['Borussia Dortmund'] = 'DOR'
POLYMARKET_TO_CODE['Inter'] = 'INT'
POLYMARKET_TO_CODE['Milan'] = 'MIL'
POLYMARKET_TO_CODE['Paris Saint-Germain'] = 'PSG'
POLYMARKET_TO_CODE['Burnley FC'] = 'BUR'
POLYMARKET_TO_CODE['Sunderland AFC'] = 'SUN'
POLYMARKET_TO_CODE['Luton Town'] = 'LUT'
POLYMARKET_TO_CODE['Sheffield United'] = 'SHU'
POLYMARKET_TO_CODE['Norwich City'] = 'NOR'
POLYMARKET_TO_CODE['Watford FC'] = 'WAT'
POLYMARKET_TO_CODE['West Bromwich Albion'] = 'WBA'
POLYMARKET_TO_CODE['Wolverhampton Wanderers'] = 'WOL'

# Kalshi variations
KALSHI_TO_CODE['Wolverhampton'] = 'WOL'
KALSHI_TO_CODE['LFC'] = 'LIV'
KALSHI_TO_CODE['BRI'] = 'BHA'
KALSHI_TO_CODE['CFC'] = 'CHE'
KALSHI_TO_CODE['Tot'] = 'TOT'

# Add self-mappings for Kalshi codes found in tickers
for code in FOOTBALL_TEAMS.keys():
    KALSHI_TO_CODE[code] = code



def normalize_team_name(name, platform='polymarket'):
    """
    Normalize team name to standard team code
    
    Args:
        name: Team name string
        platform: 'polymarket', 'kalshi', 'odds_api', 'manifold'
    
    Returns:
        Team code (e.g., 'ARS', 'LIV') or None if not found
    """
    name = name.strip()
    
    # Common cleaning for all platforms
    if name.endswith(' FC'):
        name = name[:-3].strip()
    elif name.endswith(' AFC'):
        name = name[:-4].strip()
    
    if platform == 'polymarket':
        # Handle " - More Markets" suffix
        if ' - More Markets' in name:
            name = name.replace(' - More Markets', '').strip()
            
        return POLYMARKET_TO_CODE.get(name)
    elif platform == 'kalshi':
        return KALSHI_TO_CODE.get(name)
    elif platform in ['odds_api', 'manifold']:
        return FULLNAME_TO_CODE.get(name)
    else:
        return (POLYMARKET_TO_CODE.get(name) or
                KALSHI_TO_CODE.get(name) or
                FULLNAME_TO_CODE.get(name))


def get_team_info(code):
    """Get team information by team code"""
    return FOOTBALL_TEAMS.get(code)
