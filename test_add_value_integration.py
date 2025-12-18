"""
ADD VALUE Framework Integration Test
====================================
Tests the ADD VALUE Framework integration with Papito Mamito AI
"""

import sys
sys.path.insert(0, 'apps/papito_core/src')

from papito_core.add_value import AddValueFramework, FollowerGrowthEngine
from papito_core.add_value.framework import Pillar, Decision

def test_framework():
    print("=" * 60)
    print("ADD VALUE FRAMEWORK TEST")
    print("=" * 60)
    
    # Test Framework
    framework = AddValueFramework("Papito Mamito AI")
    print(f"Agent: {framework.agent_name}")
    
    # Create a decision
    decision = framework.new_decision("Need to grow from 0 to 1000 followers")
    print(f"Decision created: {decision.situation}")
    
    # Go through 4 pillars
    framework.awareness(decision, "Currently 0 followers, no engagement")
    framework.define(decision, "Goal: Reach 1000 followers in 12 weeks")
    framework.devise(decision, "Post 3x daily + engage with Afrobeat community")
    framework.validate(decision, "Industry data shows 3x daily is optimal for growth")
    
    print(f"Ready to act: {decision.ready_to_act}")
    print(f"Progress: {decision.progress}%")
    
    # Print pillar mantras
    print("\nPillars:")
    for pillar in Pillar:
        print(f"  {pillar.name}: {pillar.mantra}")
    
    return True


def test_growth_engine():
    print()
    print("=" * 60)
    print("GROWTH ENGINE TEST")
    print("=" * 60)
    
    engine = FollowerGrowthEngine()
    progress = engine.get_campaign_progress()
    
    print(f"Phase: {progress['phase']['name']}")
    print(f"Goal: {progress['goal']} followers")
    print(f"Current: {progress['current_followers']} followers")
    print(f"Progress: {progress['progress_percentage']:.1f}%")
    
    # Evaluate action
    decision = engine.evaluate_next_action()
    print(f"\nRecommended action: {decision.action.value}")
    print(f"Priority: {decision.priority}/10")
    print(f"Expected impact: {decision.expected_impact}")
    
    if decision.add_value_decision:
        print(f"\nADD VALUE Framework Status:")
        print(f"  Ready to act: {decision.add_value_decision.ready_to_act}")
        print(f"  Progress: {decision.add_value_decision.progress}%")
    
    return True


def main():
    print()
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║                                                               ║")
    print("║   ADD VALUE FRAMEWORK™ INTEGRATION TEST                       ║")
    print("║   Value Adders World - Papito Mamito AI                       ║")
    print("║                                                               ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    try:
        test_framework()
        test_growth_engine()
        
        print()
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("🌟 ADD VALUE. WE FLOURISH & PROSPER. 🌟")
        print()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    main()
