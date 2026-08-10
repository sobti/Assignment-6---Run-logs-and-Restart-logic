#include <linux/init.h>     // init.h 헤더파일 추가
#include <linux/module.h>   // module.h 헤더파일 추가
#include <linux/kernel.h>   // kernel.h 헤더파일 추가
#include <linux/list.h>     // list.h 헤더파일 추가
#include <linux/slab.h>     // slab.h 헤더파일 추가

struct birthday
{
    int month;  // 월
    int day;    // 일
    int year;   // 년
    
    struct list_head list;  // *next, *perv 변수를 통해 리스트 노드를 연결할 수 있게 한다.
};

static LIST_HEAD(birthday_list);    // 생일 정보를 연결리스트에 담을 수 있도록, birthday_list라는 이름으로 연결리스트의 헤드 포인터(시작점)를 초기화한다.

int module_birthday_init(void) {
    struct birthday *person;    // birthday 포인터를 담을 수 있도록 선언한 임시변수이다.
    person = kmalloc(sizeof(*person), GFP_KERNEL);  // birthday 포인터의 크기만큼, 커널용 메모리를 할당한다.
    person->month = 7;
    person->day = 8;
    person->year = 1996;

    INIT_LIST_HEAD(&person->list);  // list_head의 각 항목을 초기화 한다.
    list_add_tail(&person->list, &birthday_list); // 위의 항목을 연결리스트에 추가한다.
    
    person = kmalloc(sizeof(*person), GFP_KERNEL);
    person->month = 12;
    person->day = 28;
    person->year = 2000;
    INIT_LIST_HEAD(&person->list);  // list_head의 각 항목을 초기화 한다.
    list_add_tail(&person->list, &birthday_list); // 위의 항목을 연결리스트에 추가한다.

    person = kmalloc(sizeof(*person), GFP_KERNEL);
    person->month = 2;
    person->day = 1;
    person->year = 2000;
    INIT_LIST_HEAD(&person->list);  // list_head의 각 항목을 초기화 한다.
    list_add_tail(&person->list, &birthday_list); // 위의 항목을 연결리스트에 추가한다.

    person = kmalloc(sizeof(*person), GFP_KERNEL);
    person->month = 6;
    person->day = 3;
    person->year = 1234;
    INIT_LIST_HEAD(&person->list);  // list_head의 각 항목을 초기화 한다.
    list_add_tail(&person->list, &birthday_list); // 위의 항목을 연결리스트에 추가한다.

    list_for_each_entry(person, &birthday_list, list)  // person 변수가 cursor역할을 하여 순회하라. 순회 대상은 birthday_List이다. list_head는 list라는 변수(멤버)의 이름으로 저장되어있다.
    {                                               // node를 순차적으로 접근할 수 있도록 하는 매크로이다.
        printk(KERN_INFO "person %d %d %d\n", person->month,
        person->day, person->year);   // <6> KERN_INFO 레벨에서 생일에 대한 정보 로그 출력
    }
    return 0;   // 정상적인 종료를 알림
}

void module_birthday_exit(void) {
    struct birthday *ptr, *next;    // 밑의 순회 매크로를 사용하기 위해서 cursor과 임시변수 next를 선언.
    list_for_each_entry_safe(ptr, next, &birthday_list, list)   // prt 변수가 cursor 역할을 하여 순회하라. next를 임시변수로 사용하며, 순회 대상(HEAD)은 birthday_list이다.
     {                                                          // list_head는 list라는 변수(멤버)의 이름으로 저장되어있다.
                                                                // list_for_each_entry_safe는 list_for_each_entry와 다르게 순회 중간에 node가 삭제되어도 정지하지 않는다.
        printk(KERN_INFO "Removing %d %d %d\n", ptr->month,
            ptr->day, ptr->year);   // <6> KERN_INFO 레벨에서 삭제할 생일에 대한 정보 로그 출력
        list_del(&ptr->list);   // ptr포인터에 담긴 엔트리(node)를 삭제한다.
        kfree(ptr); // 동적할당된 ptr 메모리를 반납한다.
    }
}

module_init(module_birthday_init);  // 유저레벨에서 insmod를 통해 birthday.ko를 적재할 경우, module_birthday_init 함수가 호출되도록 한다.
module_exit(module_birthday_exit);  // 유저레벨에서 rmmod를 통해 birthday.ko 모듈을 해제할 경우, module_birthday_exit 함수가 호출되도록 한다.

MODULE_LICENSE("GPL");      // birthday.ko 모듈의 라이선스를 GPL(GNU Public License)로 지정하여 오픈 소스임을 명시한다.
MODULE_DESCRIPTION("Birthday List");      // 모듈의 설명을 Birthday List로 한다.
MODULE_AUTHOR("LANI");       // 모듈 제작자를 LANI로 한다.
