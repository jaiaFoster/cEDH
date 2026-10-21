"""Narrow arithmetic traces for cited rules. Not a Magic gameplay/combo engine.
Inputs assume no relevant replacement/prevention except explicitly supplied.
"""
def simultaneous_half_events(team_life,heads=2,round_up=False):
 per_head=(team_life+1)//2 if round_up else team_life//2
 return {'individual_events':[per_head]*heads,'team_life_after':team_life-heads*per_head}
def sequential_half_upkeep(team_life,heads=2):
 events=[]
 for _ in range(heads):
  amount=(team_life+1)//2;events.append(amount);team_life-=amount
 return {'individual_events':events,'team_life_after':team_life}
def pay_life(team_life,cost,cannot_change=False):
 if cost<0 or cost>team_life or (cannot_change and cost):raise ValueError('Unpayable life cost')
 return team_life-cost

def set_single_head_life(team_life,value):
 return {'individual_life_change':value-team_life,'team_life_after':value}
def sacrifice_possible(controller,permanent_controller):return controller==permanent_controller

def opponent_draw_allowed(prior_player_draws,has_narset):return not has_narset or prior_player_draws<1

def extra_team_turns(time_votes):
 if not isinstance(time_votes,int) or time_votes<0:raise ValueError('Nonnegative vote count required')
 return time_votes

def card_draws_from_team_step(skip_effect_on_either_head=False):return (0,0) if skip_effect_on_either_head else (1,1)
