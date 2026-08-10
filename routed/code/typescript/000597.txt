import { NgModule } from '@angular/core';

// modules
import { SharedModule } from '@shared/shared.module';

// components
import { ButlerComponent } from '@butler/butler.component';
import { PurchaseOrdersContentsComponent } from '@butler/purchase-orders-contents/purchase-orders-contents.component';
import { PurchaseOrdersNewFormComponent } from '@butler/purchase-orders-new-form/purchase-orders-new-form.component';
import { PurchaseOrdersHistoriesComponent } from '@butler/purchase-orders-histories/purchase-orders-histories.component';
import { PurchaseOrdersTableComponent } from '@butler/purchase-orders-table/purchase-orders-table.component';

@NgModule({
  declarations: [
    ButlerComponent,
    PurchaseOrdersContentsComponent,
    PurchaseOrdersNewFormComponent,
    PurchaseOrdersHistoriesComponent,
    PurchaseOrdersTableComponent,
  ],
  imports: [SharedModule],
})
export class ButlerModule {}
