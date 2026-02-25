#!/usr/bin/env python3
"""
Savings Goals Tracker
- Create and track multiple savings goals
- Set target amounts and deadlines
- Track progress with visual indicators
- Suggest monthly contribution amounts
- Celebrate milestones
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

SAVINGS_GOALS = 'savings_goals.json'

class SavingsGoalsTracker:
    def __init__(self):
        self.goals = self.load_goals()
    
    def load_goals(self):
        """Load savings goals from file"""
        if Path(SAVINGS_GOALS).exists():
            with open(SAVINGS_GOALS, 'r') as f:
                return json.load(f)
        return {}
    
    def save_goals(self):
        """Save savings goals to file"""
        with open(SAVINGS_GOALS, 'w') as f:
            json.dump(self.goals, f, indent=2)
    
    def add_goal(self, name, target_amount, target_date, category='general', 
                 current_amount=0, priority='medium', notes='', interest_rate=0.0):
        """
        Add a new savings goal
        
        Args:
            name: Goal name (e.g., "Emergency Fund", "Europe Trip")
            target_amount: Target dollar amount
            target_date: Target date (YYYY-MM-DD)
            category: Type of goal (emergency, vacation, house, car, education, wedding, general)
            current_amount: Current saved amount (default 0)
            priority: high, medium, low
            notes: Additional notes
            interest_rate: Annual interest rate as decimal (e.g., 0.045 for 4.5% APY)
        """
        goal_id = name.lower().replace(' ', '_')
        
        # Calculate monthly contribution needed (accounting for compound interest)
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        months_remaining = max(1, (target_dt.year - datetime.now().year) * 12 + 
                              (target_dt.month - datetime.now().month))
        
        if interest_rate > 0:
            # With compound interest: FV = PV(1+r)^n + PMT * [((1+r)^n - 1) / r]
            # Solve for PMT (monthly payment)
            monthly_rate = interest_rate / 12
            future_value_of_current = current_amount * ((1 + monthly_rate) ** months_remaining)
            remaining_needed = target_amount - future_value_of_current
            
            if remaining_needed > 0:
                # PMT = (FV * r) / ((1+r)^n - 1)
                monthly_needed = (remaining_needed * monthly_rate) / (((1 + monthly_rate) ** months_remaining) - 1)
            else:
                monthly_needed = 0
        else:
            # No interest - simple calculation
            remaining_amount = target_amount - current_amount
            monthly_needed = remaining_amount / months_remaining if months_remaining > 0 else remaining_amount
        
        self.goals[goal_id] = {
            'name': name,
            'target_amount': target_amount,
            'current_amount': current_amount,
            'target_date': target_date,
            'category': category,
            'priority': priority,
            'notes': notes,
            'interest_rate': interest_rate,
            'created_date': datetime.now().strftime('%Y-%m-%d'),
            'monthly_contribution_needed': monthly_needed,
            'contributions': [],
            'interest_earned': 0.0,
            'milestones': self._generate_milestones(target_amount)
        }
        
        self.save_goals()
        return goal_id
    
    def _generate_milestones(self, target_amount):
        """Generate milestone markers (25%, 50%, 75%, 100%)"""
        return {
            '25%': target_amount * 0.25,
            '50%': target_amount * 0.50,
            '75%': target_amount * 0.75,
            '100%': target_amount
        }
    
    def update_goal(self, goal_id, **kwargs):
        """Update an existing goal"""
        if goal_id not in self.goals:
            return False
        
        # Update fields
        for key, value in kwargs.items():
            if key in ['name', 'target_amount', 'current_amount', 'target_date', 
                      'category', 'priority', 'notes']:
                self.goals[goal_id][key] = value
        
        # Recalculate if target_amount or target_date changed
        if 'target_amount' in kwargs or 'target_date' in kwargs:
            goal = self.goals[goal_id]
            target_dt = datetime.strptime(goal['target_date'], '%Y-%m-%d')
            months_remaining = max(1, (target_dt.year - datetime.now().year) * 12 + 
                                  (target_dt.month - datetime.now().month))
            remaining = goal['target_amount'] - goal['current_amount']
            goal['monthly_contribution_needed'] = remaining / months_remaining if months_remaining > 0 else remaining
            goal['milestones'] = self._generate_milestones(goal['target_amount'])
        
        self.save_goals()
        return True
    
    def delete_goal(self, goal_id):
        """Delete a goal"""
        if goal_id in self.goals:
            del self.goals[goal_id]
            self.save_goals()
            return True
        return False
    
    def add_contribution(self, goal_id, amount, date=None, notes=''):
        """Record a contribution to a goal"""
        if goal_id not in self.goals:
            return False
        
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        contribution = {
            'amount': amount,
            'date': date,
            'notes': notes
        }
        
        self.goals[goal_id]['contributions'].append(contribution)
        self.goals[goal_id]['current_amount'] += amount
        
        # Check if milestone reached
        milestone = self._check_milestone_reached(goal_id)
        
        self.save_goals()
        return milestone
    
    def _check_milestone_reached(self, goal_id):
        """Check if a milestone was just reached"""
        goal = self.goals[goal_id]
        current = goal['current_amount']
        target = goal['target_amount']
        progress = (current / target) * 100 if target > 0 else 0
        
        milestones = {
            '25%': 25,
            '50%': 50,
            '75%': 75,
            '100%': 100
        }
        
        for name, threshold in milestones.items():
            if progress >= threshold:
                # Check if this is the first time hitting this milestone
                if not goal.get(f'milestone_{name}_reached', False):
                    goal[f'milestone_{name}_reached'] = True
                    return name
        
        return None
    
    def apply_interest(self, goal_id, months=1):
        """
        Apply compound interest for a given period
        Useful for projecting future balance or calculating earned interest
        
        Args:
            goal_id: The goal to apply interest to
            months: Number of months to compound (default 1)
        """
        if goal_id not in self.goals:
            return False
        
        goal = self.goals[goal_id]
        interest_rate = goal.get('interest_rate', 0.0)
        
        if interest_rate <= 0:
            return False
        
        monthly_rate = interest_rate / 12
        current = goal['current_amount']
        
        # Compound interest: A = P(1 + r)^n
        new_amount = current * ((1 + monthly_rate) ** months)
        interest_earned = new_amount - current
        
        goal['current_amount'] = new_amount
        goal['interest_earned'] = goal.get('interest_earned', 0.0) + interest_earned
        
        # Log as contribution
        goal['contributions'].append({
            'amount': interest_earned,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'notes': f'Interest accrued ({months} month(s))'
        })
        
        self.save_goals()
        return interest_earned
    
    def project_with_interest(self, goal_id, monthly_contribution=None):
        """
        Project goal completion with compound interest
        Shows month-by-month balance growth
        
        Args:
            goal_id: The goal to project
            monthly_contribution: Override monthly contribution (uses calculated if None)
        """
        if goal_id not in self.goals:
            return None
        
        goal = self.goals[goal_id]
        interest_rate = goal.get('interest_rate', 0.0)
        monthly_rate = interest_rate / 12
        
        if monthly_contribution is None:
            monthly_contribution = goal['monthly_contribution_needed']
        
        target = goal['target_amount']
        balance = goal['current_amount']
        
        target_dt = datetime.strptime(goal['target_date'], '%Y-%m-%d')
        months_remaining = max(1, (target_dt.year - datetime.now().year) * 12 + 
                              (target_dt.month - datetime.now().month))
        
        projection = []
        month = 0
        total_contributed = 0
        total_interest = 0
        
        while balance < target and month < months_remaining:
            # Add contribution
            balance += monthly_contribution
            total_contributed += monthly_contribution
            
            # Apply interest
            if interest_rate > 0:
                interest = balance * monthly_rate
                balance += interest
                total_interest += interest
            
            month += 1
            
            projection.append({
                'month': month,
                'balance': balance,
                'contributed': monthly_contribution,
                'interest': interest if interest_rate > 0 else 0,
                'total_contributed': total_contributed,
                'total_interest': total_interest
            })
            
            if balance >= target:
                break
        
        completion_date = datetime.now() + timedelta(days=30*month)
        
        return {
            'months_to_complete': month,
            'completion_date': completion_date.strftime('%Y-%m-%d'),
            'total_contributed': total_contributed,
            'total_interest': total_interest,
            'final_balance': balance,
            'projection': projection,
            'interest_rate': interest_rate
        }
    
    def get_goal_summary(self, goal_id):
        """Get detailed summary of a goal"""
        if goal_id not in self.goals:
            return None
        
        goal = self.goals[goal_id]
        
        # Calculate progress
        progress_pct = (goal['current_amount'] / goal['target_amount'] * 100) if goal['target_amount'] > 0 else 0
        remaining = goal['target_amount'] - goal['current_amount']
        
        # Calculate time remaining
        target_dt = datetime.strptime(goal['target_date'], '%Y-%m-%d')
        days_remaining = (target_dt - datetime.now()).days
        months_remaining = max(0, days_remaining // 30)
        
        # Calculate if on track
        expected_by_now = goal['target_amount'] * (1 - (days_remaining / 365)) if days_remaining >= 0 else goal['target_amount']
        on_track = goal['current_amount'] >= expected_by_now * 0.9  # 90% threshold
        
        # Total contributions
        total_contributed = sum(c['amount'] for c in goal['contributions'])
        interest_earned = goal.get('interest_earned', 0.0)
        interest_rate = goal.get('interest_rate', 0.0)
        
        summary = {
            'name': goal['name'],
            'target_amount': goal['target_amount'],
            'current_amount': goal['current_amount'],
            'remaining': remaining,
            'progress_pct': progress_pct,
            'target_date': goal['target_date'],
            'days_remaining': days_remaining,
            'months_remaining': months_remaining,
            'monthly_needed': goal['monthly_contribution_needed'],
            'on_track': on_track,
            'total_contributions': len(goal['contributions']),
            'total_contributed': total_contributed,
            'interest_earned': interest_earned,
            'interest_rate': interest_rate,
            'category': goal['category'],
            'priority': goal['priority'],
            'status': self._get_status(goal)
        }
        
        return summary
    
    def _get_status(self, goal):
        """Determine goal status"""
        progress = (goal['current_amount'] / goal['target_amount']) * 100 if goal['target_amount'] > 0 else 0
        
        target_dt = datetime.strptime(goal['target_date'], '%Y-%m-%d')
        days_remaining = (target_dt - datetime.now()).days
        
        if progress >= 100:
            return 'completed'
        elif days_remaining < 0:
            return 'overdue'
        elif days_remaining < 30:
            return 'urgent'
        else:
            return 'active'
    
    def get_all_goals(self):
        """Get summary of all goals"""
        summaries = []
        for goal_id in self.goals:
            summary = self.get_goal_summary(goal_id)
            if summary:
                summary['goal_id'] = goal_id
                summaries.append(summary)
        
        return summaries
    
    def get_total_savings_target(self):
        """Get total across all goals"""
        return sum(goal['target_amount'] for goal in self.goals.values())
    
    def get_total_saved(self):
        """Get total currently saved across all goals"""
        return sum(goal['current_amount'] for goal in self.goals.values())
    
    def suggest_allocation(self, monthly_budget):
        """
        Suggest how to allocate monthly savings across goals
        Based on priority and deadline urgency
        """
        if not self.goals:
            return {}
        
        # Calculate total monthly needed
        total_needed = sum(goal['monthly_contribution_needed'] for goal in self.goals.values())
        
        if monthly_budget >= total_needed:
            # Can meet all goals
            return {
                goal_id: goal['monthly_contribution_needed']
                for goal_id, goal in self.goals.items()
            }
        
        # Need to prioritize
        allocations = {}
        remaining_budget = monthly_budget
        
        # Sort by priority and urgency
        sorted_goals = sorted(
            self.goals.items(),
            key=lambda x: (
                {'high': 0, 'medium': 1, 'low': 2}[x[1]['priority']],
                (datetime.strptime(x[1]['target_date'], '%Y-%m-%d') - datetime.now()).days
            )
        )
        
        for goal_id, goal in sorted_goals:
            if remaining_budget <= 0:
                allocations[goal_id] = 0
            else:
                needed = goal['monthly_contribution_needed']
                allocated = min(needed, remaining_budget)
                allocations[goal_id] = allocated
                remaining_budget -= allocated
        
        return allocations
    
    def get_contribution_history(self, goal_id=None, days_back=90):
        """Get contribution history, optionally filtered by goal"""
        history = []
        
        goals_to_check = [goal_id] if goal_id else self.goals.keys()
        
        for gid in goals_to_check:
            if gid not in self.goals:
                continue
            
            goal = self.goals[gid]
            for contrib in goal['contributions']:
                contrib_date = datetime.strptime(contrib['date'], '%Y-%m-%d')
                if (datetime.now() - contrib_date).days <= days_back:
                    history.append({
                        'goal': goal['name'],
                        'goal_id': gid,
                        'amount': contrib['amount'],
                        'date': contrib['date'],
                        'notes': contrib.get('notes', '')
                    })
        
        return sorted(history, key=lambda x: x['date'], reverse=True)
    
    def export_summary(self):
        """Export goals summary for reporting"""
        data = []
        for goal_id, goal in self.goals.items():
            summary = self.get_goal_summary(goal_id)
            data.append({
                'Goal': summary['name'],
                'Target': f"${summary['target_amount']:,.2f}",
                'Current': f"${summary['current_amount']:,.2f}",
                'Progress': f"{summary['progress_pct']:.1f}%",
                'Deadline': summary['target_date'],
                'Monthly Needed': f"${summary['monthly_needed']:.2f}",
                'Status': summary['status']
            })
        
        return pd.DataFrame(data)

def main():
    import sys
    
    tracker = SavingsGoalsTracker()
    
    if len(sys.argv) < 2:
        print("\n=== Savings Goals Tracker ===\n")
        print("Commands:")
        print("  add <name> <target> <date> [category] [priority]")
        print("  contribute <goal_id> <amount> [date]")
        print("  list")
        print("  detail <goal_id>")
        print("  suggest <monthly_budget>")
        print("  history [goal_id]")
        print("\nExamples:")
        print("  python savings_goals.py add 'Emergency Fund' 10000 2026-12-31 emergency high")
        print("  python savings_goals.py contribute emergency_fund 500")
        print("  python savings_goals.py suggest 1000")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'add':
        name = sys.argv[2]
        target = float(sys.argv[3])
        date = sys.argv[4]
        category = sys.argv[5] if len(sys.argv) > 5 else 'general'
        priority = sys.argv[6] if len(sys.argv) > 6 else 'medium'
        interest_rate = float(sys.argv[7]) if len(sys.argv) > 7 else 0.0
        
        goal_id = tracker.add_goal(name, target, date, category, priority=priority, interest_rate=interest_rate)
        print(f"✓ Added goal: {name} (ID: {goal_id})")
        print(f"  Target: ${target:,.2f} by {date}")
        if interest_rate > 0:
            print(f"  Interest Rate: {interest_rate * 100:.2f}% APY")
        summary = tracker.get_goal_summary(goal_id)
        print(f"  Monthly needed: ${summary['monthly_needed']:.2f}")
        if interest_rate > 0:
            print(f"  (Interest helps reduce required contribution!)")
    
    elif command == 'contribute':
        goal_id = sys.argv[2]
        amount = float(sys.argv[3])
        date = sys.argv[4] if len(sys.argv) > 4 else None
        
        milestone = tracker.add_contribution(goal_id, amount, date)
        print(f"✓ Added ${amount:.2f} to {goal_id}")
        
        if milestone:
            print(f"🎉 Milestone reached: {milestone}!")
        
        summary = tracker.get_goal_summary(goal_id)
        print(f"  Progress: {summary['progress_pct']:.1f}% (${summary['current_amount']:,.2f} / ${summary['target_amount']:,.2f})")
    
    elif command == 'list':
        goals = tracker.get_all_goals()
        
        print("\n💰 SAVINGS GOALS\n")
        print(f"{'Goal':25} {'Progress':10} {'Target':12} {'Deadline':12} {'Status':10}")
        print("-" * 80)
        
        for goal in sorted(goals, key=lambda x: x['priority']):
            status_icon = {
                'completed': '✅',
                'overdue': '⚠️',
                'urgent': '🔥',
                'active': '📊'
            }[goal['status']]
            
            print(f"{goal['name']:25} {goal['progress_pct']:5.1f}% / 100% ${goal['target_amount']:10,.2f} {goal['target_date']:12} {status_icon} {goal['status']:8}")
        
        print(f"\nTotal Target: ${tracker.get_total_savings_target():,.2f}")
        print(f"Total Saved:  ${tracker.get_total_saved():,.2f}")
    
    elif command == 'detail':
        goal_id = sys.argv[2]
        summary = tracker.get_goal_summary(goal_id)
        
        if not summary:
            print(f"Goal '{goal_id}' not found")
            return
        
        print(f"\n📊 {summary['name']}")
        print("=" * 60)
        print(f"Target:              ${summary['target_amount']:,.2f}")
        print(f"Current:             ${summary['current_amount']:,.2f}")
        print(f"Remaining:           ${summary['remaining']:,.2f}")
        print(f"Progress:            {summary['progress_pct']:.1f}%")
        print(f"\nDeadline:            {summary['target_date']}")
        print(f"Days remaining:      {summary['days_remaining']}")
        print(f"Months remaining:    {summary['months_remaining']}")
        print(f"\nMonthly needed:      ${summary['monthly_needed']:.2f}")
        print(f"Priority:            {summary['priority']}")
        print(f"Category:            {summary['category']}")
        print(f"Status:              {summary['status']}")
        print(f"On track:            {'✅ Yes' if summary['on_track'] else '⚠️ No'}")
        print(f"\nContributions:       {summary['total_contributions']} (${summary['total_contributed']:,.2f} total)")
    
    elif command == 'suggest':
        monthly_budget = float(sys.argv[2])
        allocations = tracker.suggest_allocation(monthly_budget)
        
        print(f"\n💡 SUGGESTED ALLOCATION FOR ${monthly_budget:.2f}/month\n")
        print(f"{'Goal':30} {'Suggested':12} {'Needed':12}")
        print("-" * 60)
        
        for goal_id, amount in allocations.items():
            goal = tracker.goals[goal_id]
            needed = goal['monthly_contribution_needed']
            print(f"{goal['name']:30} ${amount:10,.2f} ${needed:10,.2f}")
        
        total_allocated = sum(allocations.values())
        print(f"\n{'TOTAL':30} ${total_allocated:10,.2f}")
        
        if total_allocated < monthly_budget:
            print(f"Surplus:             ${monthly_budget - total_allocated:.2f}")
    
    elif command == 'history':
        goal_id = sys.argv[2] if len(sys.argv) > 2 else None
        history = tracker.get_contribution_history(goal_id)
        
        print("\n📝 CONTRIBUTION HISTORY\n")
        print(f"{'Date':12} {'Goal':25} {'Amount':12}")
        print("-" * 60)
        
        for contrib in history:
            print(f"{contrib['date']:12} {contrib['goal']:25} ${contrib['amount']:10,.2f}")
    
    elif command == 'project':
        goal_id = sys.argv[2]
        monthly_contrib = float(sys.argv[3]) if len(sys.argv) > 3 else None
        
        projection = tracker.project_with_interest(goal_id, monthly_contrib)
        
        if not projection:
            print(f"Goal '{goal_id}' not found")
            return
        
        print(f"\n📊 PROJECTION WITH INTEREST\n")
        print(f"Interest Rate: {projection['interest_rate'] * 100:.2f}% APY")
        print(f"Months to Complete: {projection['months_to_complete']}")
        print(f"Completion Date: {projection['completion_date']}")
        print(f"Total You'll Contribute: ${projection['total_contributed']:,.2f}")
        print(f"Total Interest Earned: ${projection['total_interest']:,.2f}")
        print(f"Final Balance: ${projection['final_balance']:,.2f}")
        
        if projection['interest_rate'] > 0:
            print(f"\n💡 Interest will earn you ${projection['total_interest']:,.2f} for free!")
        
        # Show first 12 months
        print(f"\n{'Month':6} {'Balance':12} {'Contributed':12} {'Interest':12}")
        print("-" * 50)
        for month_data in projection['projection'][:12]:
            print(f"{month_data['month']:5} ${month_data['balance']:10,.2f} ${month_data['contributed']:10,.2f} ${month_data['interest']:10,.2f}")
        
        if len(projection['projection']) > 12:
            print(f"... and {len(projection['projection']) - 12} more months")
    
    elif command == 'interest':
        goal_id = sys.argv[2]
        months = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        
        interest_earned = tracker.apply_interest(goal_id, months)
        
        if interest_earned:
            print(f"✓ Applied {months} month(s) of interest")
            print(f"  Interest earned: ${interest_earned:.2f}")
            
            summary = tracker.get_goal_summary(goal_id)
            print(f"  New balance: ${summary['current_amount']:,.2f}")
        else:
            print(f"No interest to apply (rate is 0% or goal not found)")

if __name__ == "__main__":
    main()
