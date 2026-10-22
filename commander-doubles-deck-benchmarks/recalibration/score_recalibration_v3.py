"""Offline research-only v2/v3 scorer; does not activate either schedule."""
import argparse,json,pathlib,sys
from recalibration_v3 import build_backends,load_deck,budget

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('deck_a');parser.add_argument('--deck-b')
    parser.add_argument('--model',choices=('organizer-v2','candidate-v3'),default='candidate-v3')
    parser.add_argument('--export');parser.add_argument('--summary',action='store_true')
    args=parser.parse_args()
    try:
        _,v2,v3,*_=build_backends();backend=v2 if args.model=='organizer-v2' else v3
        a=load_deck(args.deck_a)
        if args.deck_b:
            result=backend.team(a,load_deck(args.deck_b));result['construction_budget']=budget(result['a']['total'],result['b']['total'])
            # Historical backend calls a required transfer "points_transferred".
            # Do not misrepresent an infeasible requirement as an executed transfer.
            result['transfer_required']=result.pop('points_transferred')
            result['transferrable_points']=result['construction_budget']['transferrable_points']
            good=result['both_decks_legal'] and result['budget_compliant']
        else:
            result=backend.score(a);good=result['officially_legal'] and result['within_individual_cap']
        result.update(status='season0-proposed',activated=False,gameplay_legality_approved=False)
        text=json.dumps(result,indent=2,sort_keys=True)+'\n'
        if args.export:pathlib.Path(args.export).write_text(text)
        if args.summary:
            keys=('version','status','activated','total','command_zone_total','officially_legal','both_decks_legal','within_individual_cap','budget_compliant','transfer_required','transferrable_points','construction_budget','gameplay_legality_approved')
            print(json.dumps({k:result[k] for k in keys if k in result},indent=2))
        else:print(text,end='')
        return 0 if good else 1
    except (ValueError,KeyError,OSError) as error:
        print('ERROR: '+str(error),file=sys.stderr);return 2

if __name__=='__main__':sys.exit(main())
