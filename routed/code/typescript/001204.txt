import { Component, OnInit } from '@angular/core';
import { CourseService } from '../service/courseservice';
import { Course } from '../service/course';
import { Users } from '../service/users';
import { ConfirmationService } from 'primeng/api';
import { MessageService } from 'primeng/api';
import * as FileSaver from 'file-saver';
import * as XLSX from 'xlsx';
import {SelectItem} from 'primeng/api';
import { toBase64String } from '@angular/compiler/src/output/source_map';


@Component({
  selector: 'app-table-list',
  templateUrl: './table-list.component.html',
  styleUrls: ['./table-list.component.css']
})
export class TableListComponent implements OnInit {
  op:boolean;

  productDialog: boolean;

  products: Course[];

  product: Course;

  selectedProducts: Course[];

  selectedUsers: any;

  submitted: boolean;

  exportColumns: any[];

  registerCourse : boolean;

  users : Users[];
  
  user : Users;

  statuses: SelectItem[];

  RegisterDialog : boolean;

  submitRegister: boolean;

  registerUser = {_id : '',course :""};

  error = null;

  erroruser = null;

  selectedcourse:string = null;
  
  header = {course :""};

  category: SelectItem[];
               
  constructor(
    private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private courseService: CourseService) { }

  ngOnInit() {
    this.courseService.getCourse().subscribe(data => this.products = data);
    this.statuses = [{label: 'ลงทะเบียน', value: 'ลงทะเบียน'},{label: 'อบรมแล้ว', value: 'อบรมแล้ว'},{label: 'ขาดอบรม', value: 'ขาดอบรม'}]
    this.category = [{label: 'ความรู้', value: 'ความรู้'},{label: 'ทักษะ', value: 'ทักษะ'},{label: 'ทัศนคติ', value: 'ทัศนคติ'}]
  }

  openNew() {
    this.product = {};
    this.submitted = false;
    this.productDialog = true;
  }

  RegisterUser() {
    this.error = null;
    this.registerUser._id = null;
    this.submitRegister = false;
    this.RegisterDialog = true;
  }

  hideRegisterCourse(){
    this.registerCourse = false;
  }

  hideRegister(){
    this.registerUser._id = null;
    this.RegisterDialog = false;
    this.submitRegister = false;
  }
  saveRegisterCourse(){
    this.users.forEach(element => {
      element['course'] = this.selectedcourse
    });
    this.courseService.updateCourseRegister(this.users).subscribe((data: {
      
    }) => {
      this.messageService.add({ severity: 'success', summary: 'Successful', detail: 'Updated Success', life: 3000 });
      this.registerCourse = false;
    },(error:any)=> this.error = error.error.error);
  }


  saveRegister(id:string){
    this.submitRegister = true;
    this.registerUser._id = id;
    this.courseService.addRegisterUser(this.registerUser).subscribe((data: {}) => {
      this.courseService.getCourse().subscribe(data => this.products = data);
      this.RegisterDialog = false;
      this.courseService.getRegisterUser(this.registerUser.course).subscribe((data=>this.users = data),(error:any)=>this.erroruser = error.error.error);
      this.messageService.add({ severity: 'success', summary: 'Successful', detail: 'User Updated', life: 3000 });
      this.registerUser._id = null;
    },(error:any)=> this.error = error.error.error);
  }

  deleteSelectRegister(){
    this.confirmationService.confirm({
      message: 'Are you sure you want to delete the selected User?',
      header: 'Confirm',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.selectedUsers.forEach(element => {
          element['course'] = this.selectedcourse
        });
        this.courseService.selectDeleteUserRegister(this.selectedUsers).subscribe(data=>{this.courseService.getCourse().subscribe(data => this.products = data);})
        this.users = this.users.filter(val => !this.selectedUsers.includes(val));
        this.selectedUsers = null;
        this.selectedcourse = null;
        this.messageService.add({ severity: 'success', summary: 'Successful', detail: 'User Deleted', life: 3000 });
        this.editCourseUser(this.selectedUsers);
        this.hideRegisterCourse();
     
      }
    });
  
  }



  editCourseUser(product:Course){
    this.header.course = product.course;
    this.selectedcourse = product._id;
    this.registerUser.course = product._id;
    this.user = {};
    this.users = [];
    this.registerCourse = true;
    this.courseService.getRegisterUser(product._id).subscribe((data=>this.users = data),(error:any)=>this.erroruser = error.error.error);
  }

  deleteSelectedProducts() {
    this.confirmationService.confirm({
      message: 'Are you sure you want to delete the selected Course?',
      header: 'Confirm',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.courseService.selectDelete(this.selectedProducts).subscribe()
        this.products = this.products.filter(val => !this.selectedProducts.includes(val));
        this.selectedProducts = null;
        this.messageService.add({ severity: 'success', summary: 'Successful', detail: 'Products Deleted', life: 3000 });
      }

    });
  }
  editProduct(product: Course) {
    this.product = { ...product };
    this.productDialog = true;

  }


  deleteProduct(product: Course) {
    this.confirmationService.confirm({
      message: 'Are you sure you want to delete ' + product.course + '?',
      header: 'Confirm',
      icon: 'pi pi-exclamation-triangle',

      accept: () => {
        this.courseService.deleteCourse(product._id).subscribe();
        this.products = this.products.filter(val => val._id !== product._id);
        this.product = {}
        this.messageService.add({ severity: 'success', summary: 'Successful', detail: 'Product Deleted', life: 3000 });
      }
    });
  }
  
 

  hideDialog() {
    this.productDialog = false;
    this.submitted = false;
  }
  // saveProduct() {

  //     this.courseService.addCourse(this.product).subscribe((data:{})=>{
  //         this.messageService.add({ severity: 'success', summary: 'Successful', detail: 'Product Updated', life: 3000 });
  //         this.submitted = true;
  //         this.productDialog = false;
  //         // this.getCourse();
  //     });


  // }

  saveProduct() {
    this.submitted = true;

    if (this.product.course.trim()) {
      if (this.product._id) {
        this.courseService.updateCourse(this.product).subscribe((data: {}) => {
          this.products[this.findIndexById(this.product._id)] = this.product;
          this.messageService.add({ severity: 'success', summary: 'Successful', detail: 'Product Updated', life: 3000 });
          this.courseService.getCourse().subscribe(data => this.products = data);
        });

      }
      else {
        this.courseService.addCourse(this.product).subscribe((data: {}) => {
          this.messageService.add({ severity: 'success', summary: 'Successful', detail: 'Product Created', life: 3000 });
          this.submitted = true;
          this.productDialog = false;
          this.courseService.getCourse().subscribe(data => this.products = data);

        });
      }

      this.products = [...this.products];
      this.productDialog = false;
      this.product = {};
    }
  }



  findIndexById(id: string): number {
    let index = -1;
    for (let i = 0; i < this.products.length; i++) {
      if (this.products[i]._id === id) {
        index = i;
        break;
      }
    }

    return index;
  }

  createId(): string {
    let id = '';
    var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (var i = 0; i < 10; i++) {
      id += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return id;
  }

  exportExcel() {
   
    import("xlsx").then(xlsx => {
      const worksheet = xlsx.utils.json_to_sheet(this.products);
      const workbook = { Sheets: { 'data': worksheet }, SheetNames: ['data'] };
      const excelBuffer: any = xlsx.write(workbook, { bookType: 'xlsx', type: 'array' });
      this.saveAsExcelFile(excelBuffer, "products");
    });
  }

  exportExcelRegister() {
    import("xlsx").then(xlsx => {
      const worksheet = xlsx.utils.json_to_sheet(this.users);
      const workbook = { Sheets: { [this.header.course]: worksheet }, SheetNames: [this.header.course] };
      const excelBuffer: any = xlsx.write(workbook, { bookType: 'xlsx', type: 'array' });
      this.saveAsExcelFile(excelBuffer, "รายชื่อลงทะเบียนอบรม");
    });
  }

  saveAsExcelFile(buffer: any, fileName: string): void {
    let EXCEL_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8';
    let EXCEL_EXTENSION = '.xlsx';
    const data: Blob = new Blob([buffer], {
      type: EXCEL_TYPE
    });
    FileSaver.saveAs(data, fileName + '_export_' + new Date().getTime() + EXCEL_EXTENSION);
  }

  opNew(){
    this.op = false;
  }
}
