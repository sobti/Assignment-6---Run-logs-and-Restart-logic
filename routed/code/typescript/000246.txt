import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import { PageEvent } from '@angular/material/paginator';

@Component({
  selector: 'app-params-form',
  template: `
    <mat-paginator [length]="10000"
                   [pageSize]="size"
                   [pageIndex]="pageIndex"
                   [pageSizeOptions]="sizes"
                   (page)="loadDataPage($event)"

    >
    </mat-paginator>
  `,
  styles: [
  ]
})
export class ParamsFormComponent implements OnInit {

  @Input()
  size: number;

  @Output()
  nextSize = new EventEmitter<number>();

  sizes = [10, 25, 50, 100, 200, 500];
  pageIndex = 0;
  constructor() { }

  ngOnInit(): void {
  }

  loadDataPage(page: PageEvent) {
    console.log('Load page', page);
    this.pageIndex = page.pageIndex;
    this.size = page.pageSize;
    this.nextSize.next(page.pageSize);
  }

}
