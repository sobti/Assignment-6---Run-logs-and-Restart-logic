<?php

namespace App\Http\Controllers\admin\settings\rbac;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Spatie\Permission\Models\Permission;
use App\Http\Requests\StorePermission;
use App\Http\Requests\UpdatePermission;
use Illuminate\Support\Facades\Auth;
use JavaScript;

class PermissionController extends Controller
{
    /**
     * Display a listing of the resource.
     *
     * @return \Illuminate\Http\Response
     */
    public function index()
    {
        return \View::make('admin.settings.rbac.permissions.permissions-list');

    }

    /**
     * Show the form for creating a new resource.
     *
     * @return \Illuminate\Http\Response
     */
    public function create()
    {
        return \View::make('admin.settings.rbac.permissions.permission-create');

    }

    /**
     * Store a newly created resource in storage.
     *
     * @param  \Illuminate\Http\Request  $request
     * @return \Illuminate\Http\Response
     */
    public function store(StorePermission $request)
    {
        $validatedData = $request->validated();

        $data = array(
            array('name' => $validatedData['permission'].' create' , 'guard_name' => 'web' , 'status' => '1' , 'created_by' => Auth::id() , 'created_at'=> date('Y-m-d H:i:s') , 'updated_at' => date('Y-m-d H:i:s')),
            array('name' => $validatedData['permission'].' view' , 'guard_name' => 'web' , 'status' => '1' , 'created_by' => Auth::id()  ,'created_at'=> date('Y-m-d H:i:s') , 'updated_at' => date('Y-m-d H:i:s')),
            array('name' => $validatedData['permission'].' edit' , 'guard_name' => 'web' , 'status' => '1' , 'created_by' => Auth::id()  ,'created_at'=> date('Y-m-d H:i:s') , 'updated_at' => date('Y-m-d H:i:s')),
            array('name' => $validatedData['permission'].' delete' , 'guard_name' => 'web', 'status' => '1' , 'created_by' => Auth::id()  , 'created_at'=> date('Y-m-d H:i:s') , 'updated_at' => date('Y-m-d H:i:s')),
        );

        if(Permission::insert($data)){

            return \response()->json(['status'=>'true' , 'message'=>'Permission added successfully' ]);

        }else{

            return \response()->json(['status'=>'error' , 'message'=>'error occured ! please try agin' ]);
        }

    }

    /**
     * Display the specified resource.
     *
     * @param  int  $id
     * @return \Illuminate\Http\Response
     */
    public function show($id)
    {
        //
    }

    /**
     * Show the form for editing the specified resource.
     *
     * @param  int  $id
     * @return \Illuminate\Http\Response
     */
    public function edit($id)
    {
        JavaScript::put([
            'id' => $id,
        ]);
        $singlRecord  =  PErmission::find($id);
        return \View::make('admin.settings.rbac.permissions.permission-edit' , compact('singlRecord'));

    }

    /**
     * Update the specified resource in storage.
     *
     * @param  \Illuminate\Http\Request  $request
     * @param  int  $id
     * @return \Illuminate\Http\Response
     */
    public function update(Request $request, $id)
    {
        // $validatedData = $request->validated();

        // $roleModel = Role::find($id);

        // $roleModel->name = $validatedData['role'];
        // $roleModel->updated_by = Auth::id();

        // if($roleModel->save()){
        //     return response()->json(['status'=>'true' , 'message' => 'Role updated successfully.'] , 200);

        // }else{
        //     return response()->json(['status'=>'true' , 'message' => 'Error! Please try again.'] , 200);

        // }
    }

    /**
     * Remove the specified resource from storage.
     *
     * @param  int  $id
     * @return \Illuminate\Http\Response
     */
    public function destroy($id)
    {
        $deleteRecord =  PErmission::find($id);

        if($deleteRecord->delete()){
            return response()->json('Your Permission has been deleted.' , 200);

        }else{
            return response()->json('error occured please try again' , 200);

        }
    }


    // ************************* datatable *******************

    public function datatable()
    {
        return \response()->json(Permission::all() , 200);

    }

        // ********************** change status **********************

        public function ChangeStatus(Request $request)
        {
            $changeStatus =  Permission::find($request->id);
            $changeStatus->status = ( ($request->status == '0') ? '0' : '1');

            if($changeStatus->save()){
                return response()->json('You change the status of permission successfully.' , 200);

            }else{
                return response()->json(  'error occured please try again' , 200);

            }

        }

}
