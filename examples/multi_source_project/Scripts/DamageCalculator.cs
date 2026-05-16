namespace Combat.Systems;

public static class DamageCalculator
{
    public static int Calculate(int heroId, int weaponId)
    {
        return HeroTable.Attack + WeaponConfig.AttackBonus;
    }
}
