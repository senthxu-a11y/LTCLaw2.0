local CharacterGrowthService = {}

function CharacterGrowthService.apply_level(heroId, level)
    return HeroTable.HP + level
end

return CharacterGrowthService
