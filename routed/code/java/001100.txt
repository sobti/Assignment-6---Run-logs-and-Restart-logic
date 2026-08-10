package goodtrailer.adventtic.smeltery;

import java.util.function.Consumer;

import goodtrailer.adventtic.AdventTiC;
import goodtrailer.adventtic.fluids.AdventTiCFluids;
import net.minecraft.block.Block;
import net.minecraft.data.DataGenerator;
import net.minecraft.data.IFinishedRecipe;
import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityType;
import net.minecraft.item.Item;
import net.minecraft.item.crafting.Ingredient;
import net.minecraft.util.IItemProvider;
import net.minecraftforge.fluids.FluidStack;
import net.minecraftforge.fluids.ForgeFlowingFluid;
import net.minecraftforge.fml.RegistryObject;
import net.minecraftforge.registries.IForgeRegistryEntry;
import net.tslat.aoa3.common.registration.AoABlocks;
import net.tslat.aoa3.common.registration.AoAEntities;
import net.tslat.aoa3.common.registration.AoAItems;
import net.tslat.aoa3.common.registration.AoATools;
import net.tslat.aoa3.common.registration.AoAWeapons;
import slimeknights.mantle.recipe.EntityIngredient;
import slimeknights.mantle.registration.object.FluidObject;
import slimeknights.tconstruct.common.data.BaseRecipeProvider;
import slimeknights.tconstruct.library.data.recipe.ISmelteryRecipeHelper;
import slimeknights.tconstruct.library.recipe.FluidValues;
import slimeknights.tconstruct.library.recipe.entitymelting.EntityMeltingRecipeBuilder;
import slimeknights.tconstruct.library.recipe.melting.MeltingRecipeBuilder;

public class AdventTiCMeltingRecipeProvider extends BaseRecipeProvider
        implements ISmelteryRecipeHelper
{
    public static final String NAME = "AdventTiC Melting Recipes";
    public static final String FOLDER = "smeltery/melting/";

    public AdventTiCMeltingRecipeProvider(DataGenerator gen)
    {
        super(gen);
    }

    @Override
    public String getName()
    {
        return NAME;
    }

    @Override
    public String getModId()
    {
        return AdventTiC.MOD_ID;
    }

    @Override
    protected void buildShapelessRecipes(Consumer<IFinishedRecipe> con)
    {
        metal(con, AdventTiCFluids.MOLTEN_BARONYTE, AdventTiCByproducts.VARSIUM);
        metal(con, AdventTiCFluids.MOLTEN_BLAZIUM, AdventTiCByproducts.BARONYTE);
        metal(con, AdventTiCFluids.MOLTEN_ELECANIUM);
        metal(con, AdventTiCFluids.MOLTEN_EMBERSTONE);
        metal(con, AdventTiCFluids.MOLTEN_GHASTLY, AdventTiCByproducts.GHOULISH);
        metal(con, AdventTiCFluids.MOLTEN_GHOULISH, AdventTiCByproducts.GHASTLY);
        metal(con, AdventTiCFluids.MOLTEN_LIMONITE, AdventTiCByproducts.ROSITE);
        metal(con, AdventTiCFluids.MOLTEN_LUNAR);
        metal(con, AdventTiCFluids.MOLTEN_LYON);
        metal(con, AdventTiCFluids.MOLTEN_MYSTITE);
        metal(con, AdventTiCFluids.MOLTEN_ROSITE, AdventTiCByproducts.LIMONITE);
        metal(con, AdventTiCFluids.MOLTEN_SHYRESTONE);
        metal(con, AdventTiCFluids.MOLTEN_SKELETAL);
        metal(con, AdventTiCFluids.MOLTEN_VARSIUM, AdventTiCByproducts.BARONYTE);

        tools(con, AdventTiCFluids.MOLTEN_EMBERSTONE, AoATools.EMBERSTONE_SHOVEL,
                AoAWeapons.EMBERSTONE_SWORD, AoATools.EMBERSTONE_AXE, AoATools.EMBERSTONE_PICKAXE);
        tools(con, AdventTiCFluids.MOLTEN_LIMONITE, AoATools.LIMONITE_SHOVEL,
                AoAWeapons.LIMONITE_SWORD, AoATools.LIMONITE_AXE, AoATools.LIMONITE_PICKAXE);
        tools(con, AdventTiCFluids.MOLTEN_ROSITE, AoATools.ROSITE_SHOVEL,
                AoAWeapons.ROSITE_SWORD, AoATools.ROSITE_AXE, AoATools.ROSITE_PICKAXE);

        lamp(con, AdventTiCFluids.MOLTEN_BARONYTE, AoABlocks.BARONYTE_LAMP);
        lamp(con, AdventTiCFluids.MOLTEN_BLAZIUM, AoABlocks.BLAZIUM_LAMP);
        lamp(con, AdventTiCFluids.MOLTEN_ELECANIUM, AoABlocks.ELECANIUM_LAMP);
        lamp(con, AdventTiCFluids.MOLTEN_EMBERSTONE, AoABlocks.EMBERSTONE_LAMP);
        lamp(con, AdventTiCFluids.MOLTEN_GHASTLY, AoABlocks.GHASTLY_LAMP);
        lamp(con, AdventTiCFluids.MOLTEN_GHOULISH, AoABlocks.GHOULISH_LAMP);
        lamp(con, AdventTiCFluids.MOLTEN_LIMONITE, AoABlocks.LIMONITE_LAMP);
        lamp(con, AdventTiCFluids.MOLTEN_LYON, AoABlocks.LYON_LAMP);
        lamp(con, AdventTiCFluids.MOLTEN_MYSTITE, AoABlocks.MYSTIC_LAMP);
        lamp(con, AdventTiCFluids.MOLTEN_ROSITE, AoABlocks.ROSITE_LAMP);

        items(con, AdventTiCFluids.MOLTEN_BARONYTE, "sword", 2 * FluidValues.INGOT,
                AoAWeapons.BARON_SWORD);
        items(con, AdventTiCFluids.MOLTEN_LIMONITE, "rod", 1 * FluidValues.INGOT,
                AoAItems.LIMONITE_ROD);
        items(con, AdventTiCFluids.MOLTEN_LIMONITE, "cannonball", 3 * FluidValues.NUGGET,
                AoAItems.CANNONBALL);
        items(con, AdventTiCFluids.MOLTEN_SKELETAL, "bow", 3 * FluidValues.INGOT,
                AoAWeapons.SKELETAL_BOW);
        items(con, AdventTiCFluids.MOLTEN_CHARGER, "raw_shank", 17,
                AdventTiCByproducts.SHYRESTONE_LESS, AoAItems.RAW_CHARGER_SHANK);
        items(con, AdventTiCFluids.MOLTEN_CHARGER, "cooked_shank", 20,
                AdventTiCByproducts.SHYRESTONE, AoAItems.COOKED_CHARGER_SHANK);

        entities(con, AdventTiCFluids.MOLTEN_CHARGER, "charger", 6, 2, AoAEntities.Mobs.CHARGER,
                AoAEntities.Mobs.DESERT_CHARGER, AoAEntities.Mobs.HILL_CHARGER,
                AoAEntities.Mobs.SEA_CHARGER, AoAEntities.Mobs.SNOW_CHARGER,
                AoAEntities.Mobs.SWAMP_CHARGER, AoAEntities.Mobs.VOID_CHARGER);
        entities(con, AdventTiCFluids.MOLTEN_CHARGER, "king_charger", 16, 2,
                AoAEntities.Mobs.KING_CHARGER);
    }

    private void metal(Consumer<IFinishedRecipe> con, FluidObject<ForgeFlowingFluid> molten,
            AdventTiCByproducts.Byproduct... byproduct)
    {
        String mat = molten.getId().getPath().substring(AdventTiCFluids.MOLTEN_PREFIX.length());
        metalMelting(con, molten.get(), mat, true, FOLDER, true, byproduct);
    }

    private void tools(Consumer<IFinishedRecipe> con, FluidObject<ForgeFlowingFluid> molten,
            RegistryObject<Item> shovel, RegistryObject<Item> sword, RegistryObject<Item> axe,
            RegistryObject<Item> pickaxe)
    {
        items(con, molten, "shovel", 1 * FluidValues.INGOT, shovel);
        items(con, molten, "sword", 2 * FluidValues.INGOT, sword);
        items(con, molten, "axes", 3 * FluidValues.INGOT, axe, pickaxe);
    }

    private void lamp(Consumer<IFinishedRecipe> con, FluidObject<ForgeFlowingFluid> molten,
            RegistryObject<Block> lamp)
    {
        items(con, molten, "lamp", 1 * FluidValues.INGOT, lamp);
    }

    @SafeVarargs
    private final <T extends IForgeRegistryEntry<? super T> & IItemProvider> void items(
            Consumer<IFinishedRecipe> con, FluidObject<ForgeFlowingFluid> molten, String name,
            int amount, RegistryObject<T> item, RegistryObject<T>... items)
    {
        items(con, molten, name, amount, null, item, items);
    }

    @SafeVarargs
    private final <T extends IForgeRegistryEntry<? super T> & IItemProvider> void items(
            Consumer<IFinishedRecipe> con, FluidObject<ForgeFlowingFluid> molten, String name,
            int amount, AdventTiCByproducts.Byproduct byproduct,
            RegistryObject<T> item, RegistryObject<T>... items)
    {
        String mat = molten.getId().getPath().substring(AdventTiCFluids.MOLTEN_PREFIX.length());
        FluidStack output = new FluidStack(molten.get(), amount);

        IItemProvider[] itemProviders = new IItemProvider[items.length + 1];
        itemProviders[0] = item.get();
        for (int i = 0; i < items.length; i++)
            itemProviders[i + 1] = items[i].get();

        MeltingRecipeBuilder builder = MeltingRecipeBuilder.melting(Ingredient.of(itemProviders),
                output, amount);

        if (byproduct != null)
            builder.addByproduct(new FluidStack(byproduct.getFluid(), byproduct.getNuggets()));

        builder.build(con, modResource(FOLDER + mat + "/" + name));
    }

    @SafeVarargs
    private final <T extends Entity> void entities(Consumer<IFinishedRecipe> con,
            FluidObject<ForgeFlowingFluid> molten, String name, int amount, int damage,
            RegistryObject<EntityType<T>> entity, RegistryObject<EntityType<T>>... entities)
    {
        String mat = molten.getId().getPath().substring(AdventTiCFluids.MOLTEN_PREFIX.length());

        EntityType<?>[] entityTypes = new EntityType<?>[entities.length + 1];
        entityTypes[0] = entity.get();
        for (int i = 0; i < entities.length; i++)
            entityTypes[i + 1] = entities[i].get();

        FluidStack output = new FluidStack(molten.get(), amount);
        EntityMeltingRecipeBuilder.melting(EntityIngredient.of(entityTypes), output, damage)
                .build(con, modResource(FOLDER + mat + "/" + name));
    }
}
