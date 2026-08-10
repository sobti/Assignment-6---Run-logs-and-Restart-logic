<?php

namespace App\Http\Models\Transaksi\Detail;

use App\Http\Models\Feed\Resource\FeedModel;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\QueryException;
use Illuminate\Support\Facades\DB;
use Yajra\DataTables\DataTables;

class TransaksiModel extends Model
{
    protected $table = 'tbl_dtl_transaksi';
    protected $primaryKey = 'id_transaksi';
    protected $view = 'vw_dtl_transaksi';
    protected $guards = [
        "id_transaksi",
        "created_at"
    ];
    protected $fillable = [
        'id_payment',
        'id_feed',
        'jenis_transaksi',
        'status_transaksi',
        'saldo_transaksi',
        "created_by",
        'updated_by',
        'updated_at',
    ];
    protected $dates = [
        "created_at",
        'updated_at'
    ];

    private $status_not_set = 0;
    private $status_success = 1;
    private $status_cancel = 2;
    private $status_expired = 3;

    /**
     * Mengambil semua data yang ada
     * Method   : GET
     *
     * @return void
     */
    public function getAll()
    {
        try {
            $data = self::get();
            $status = [
                'code' => 200,
                'status' => 'OK',
                'message' => 'Data Berhasil Dibaca',
                'data' => $data
            ];
        } catch (QueryException $error) {
            $status = [
                'code' => 500,
                'status' => 'Internal Server Error',
                'message' => $error
            ];
        }
        return $status;
    }

    /**
     * Mengambil data berdasarkan primary key
     * Method   : GET
     *
     * @param [type] $id
     * @return void
     */
    public function getById($id)
    {
        try {
            $data = DB::table($this->view)->where($this->primaryKey, $id)->first();
            $status = [
                'code' => 200,
                'status' => 'OK',
                'message' => 'Data Berhasil Dibaca',
                'data' => $data
            ];
        } catch (QueryException $error) {
            $status = [
                'code' => 500,
                'status' => 'Internal Server Error',
                'message' => $error
            ];
        }
        return $status;
    }

    /**
     * Mengambil data di tong sampah
     * Method   : GET
     *
     * @return void
     */
    public function getTrashed()
    {
        try {
            $data = self::onlyTrashed()->get();
            $status = [
                'code' => 200,
                'status' => 'OK',
                'message' => 'Data Berhasil Dibaca',
                'data' => $data
            ];
        } catch (QueryException $error) {
            $status = [
                'code' => 500,
                'status' => 'Internal Server Error',
                'message' => $error
            ];
        }
        return $status;
    }

    /**
     * Mengubah data berdasarkan primary key
     * Method   : PUT
     *
     * @param [type] $array_data
     * @return array
     */
    public function updateById($array_data)
    {
        try {
            self::where($this->primaryKey, $array_data[$this->primaryKey])
                ->update([
                    "saldo_transaksi" => $array_data['saldo_transaksi'],
                    'proses_by' => $array_data['updated_by'],
                    'proses_at' => date("Y-m-d H:i:s")
                ]);
            $status = [
                'code' => 200,
                'status' => 'OK',
                'message' => 'Data Berhasil Diubah',
                'data' => $array_data
            ];
        } catch (QueryException $error) {
            $status = [
                'code' => 500,
                'status' => 'Internal Server Error',
                'message' => $error
            ];
        }
        return $status;
    }

    /**
     * Membuat sebuah data
     * Method   : POST
     *
     * @param [type] $array_data
     * @return array
     */
    public function insertSetData($request_data)
    {
        try {
            $query = self::create([
                'id_payment' => $request_data['id_payment'],
                'jenis_transaksi' => $request_data['jenis_transaksi'],
                'saldo_transaksi' => $request_data['saldo_transaksi'],
                'created_by' => $request_data['created_by']
            ]);
            $status = [
                'code' => 200,
                'status' => 'OK',
                'message' => 'Data Berhasil Dibuat',
                'data' => $query->id_transaksi
            ];
        } catch (QueryException $error) {
            $status = [
                'code' => 500,
                'status' => 'Internal Server Error',
                'message' => $error
            ];
        }
        return $status;
    }

    public function donasiUang($request_data)
    {
        try {
            $query = self::create([
                'id_feed' => $request_data['id_feed'],
                'jenis_transaksi' => $request_data['jenis_transaksi'],
                'saldo_transaksi' => $request_data['saldo_transaksi'],
                'status_transaksi' => $request_data['status_transaksi'],
                'created_by' => $request_data['created_by']
            ]);

            /**
             * Update Saldo
             */
            $fetch_saldo = DB::table('tbl_rsc_dompet')
                ->select('id_users', 'saldo_dompet')
                ->where('id_users', $request_data['created_by'])
                ->first();
            $saldo_sebelumnya = (int)$fetch_saldo->saldo_dompet;
            $saldo_setelah = $saldo_sebelumnya-(int)$request_data['saldo_transaksi'];
            DB::table('tbl_rsc_dompet')
                ->where('id_users', $request_data['created_by'])
                ->update([
                    'saldo_dompet' => $saldo_setelah,
                    'updated_by' => $request_data['created_by'],
                    'updated_at' => date("Y-m-d H:i:s")
                ]);

            $status = [
                'code' => 200,
                'status' => 'OK',
                'message' => 'Data Berhasil Dibuat',
                'data' => $query->id_transaksi
            ];
        } catch (QueryException $error) {
            $status = [
                'code' => 500,
                'status' => 'Internal Server Error',
                'message' => $error
            ];
        }
        return $status;
    }

    public function getFeedDonasiUang($id, $offset = 0, $limit = 3)
    {
        try {
            $data = DB::table($this->view)
                ->select('id_transaksi', 'id_feed', 'saldo_transaksi', 'nama_users', 'created_at', 'foto_users')
                ->whereNotNull('id_feed')
                ->where('id_feed', $id)
                ->where('jenis_transaksi', 2)
                ->orderBy('created_at', 'desc')
                ->skip($offset)
                ->take($limit)
                ->get();
            $status = [
                'code' => 200,
                'status' => 'OK',
                'message' => 'Data Berhasil Dibaca',
                'data' => $data
            ];
        } catch (QueryException $error) {
            $status = [
                'code' => 500,
                'status' => 'Internal Server Error',
                'message' => $error
            ];
        }
        return $status;
    }

    public function countFeedDonasiUang($id) {
        try {
            $data = DB::table($this->view)
                ->select('id_transaksi')
                ->whereNotNull('id_feed')
                ->where('id_feed', $id)
                ->where('jenis_transaksi', 2)
                ->orderBy('created_at', 'desc')
                ->get();
            $status = [
                'code' => 200,
                'status' => 'OK',
                'message' => 'Data Berhasil Dibaca',
                'data' => $data->count()
            ];
        } catch (QueryException $error) {
            $status = [
                'code' => 500,
                'status' => 'Internal Server Error',
                'message' => $error
            ];
        }
        return $status;
    }

    /**
     * Membuat sebuah data
     * Method   : POST
     *
     * @param [type] $array_data
     * @return array
     */
    public function createPenarikan($request_data)
    {
        try {
            $query = self::create([
                'jenis_transaksi' => $request_data['jenis_transaksi'],
                'saldo_transaksi' => $request_data['saldo_transaksi'],
                'created_by' => $request_data['created_by']
            ]);
            $status = [
                'code' => 200,
                'status' => 'OK',
                'message' => 'Data Berhasil Dibuat',
                'data' => $query->id_transaksi
            ];
        } catch (QueryException $error) {
            $status = [
                'code' => 500,
                'status' => 'Internal Server Error',
                'message' => $error
            ];
        }
        return $status;
    }

    public function getByCreatedBy($id, $offset = 0, $limit = 6)
    {
        try {
            $data = DB::table($this->view)
                ->where('created_by', $id)
                ->skip($offset)
                ->take($limit)
                ->orderBy('created_at', 'desc')
                ->get();
            $status = [
                'code' => 200,
                'status' => 'OK',
                'message' => 'Data Berhasil Dibaca',
                'data' => $data
            ];
        } catch (QueryException $error) {
            $status = [
                'code' => 500,
                'status' => 'Internal Server Error',
                'message' => $error
            ];
        }
        return $status;
    }

    public function dataTableQueryTransaksiLandingById($id)
    {
        $query = DB::table($this->view)
            ->select('id_transaksi', 'saldo_transaksi', 'status_transaksi', 'jenis_transaksi', 'created_at')
            ->orderBy('created_at', 'desc')
            ->where('created_by', $id);
        $data_table = Datatables::of($query)
            ->addColumn('action', function ($data) {
                return '<div class="btn-group">
                <a href="' . route('dompet.transaksi.detail') . '?id=' . encrypt($data->id_transaksi) . '" class="btn btn-xs btn-complete"><i class="fa fa-search"></i> Detail</a>
                </div>
                ';
            })->make(true);
        return $data_table;
    }

    public function dataTableTopup()
    {
        $query = DB::table($this->view)
            ->select('id_transaksi', 'saldo_transaksi', 'status_transaksi', 'jenis_transaksi', 'created_at', 'nama_users')
            ->orderBy('created_at', 'desc')
            ->where('jenis_transaksi', 1);
        $data_table = Datatables::of($query)
            ->addColumn('action', function ($data) {
                return '<div class="btn-group">
                <a href="' . route('transaksi.topup.detail') . '?id=' . encrypt($data->id_transaksi) . '" class="btn btn-xs btn-complete"><i class="fa fa-search"></i> Detail</a>
                </div>
                ';
            })->make(true);
        return $data_table;
    }

    public function updateTopup($array_data)
    {
        try {
            self::where($this->primaryKey, $array_data[$this->primaryKey])
                ->update([
                    "status_transaksi" => $array_data['status_transaksi'],
                    'updated_by' => $array_data['updated_by'],
                    'updated_at' => date("Y-m-d H:i:s")
                ]);

            if ($array_data['status_transaksi'] == $this->status_success) {
                $fetch_saldo = DB::table('tbl_rsc_dompet')
                    ->select('id_users', 'saldo_dompet')
                    ->where('id_users', $array_data['created_by'])
                    ->first();
                $saldo_sebelumnya = (int)$fetch_saldo->saldo_dompet;
                $saldo_setelah = $saldo_sebelumnya+(int)$array_data['saldo_transaksi'];
                DB::table('tbl_rsc_dompet')
                    ->where('id_users', $array_data['created_by'])
                    ->update([
                        'saldo_dompet' => $saldo_setelah,
                        'updated_by' => $array_data['updated_by'],
                        'updated_at' => date("Y-m-d H:i:s")
                    ]);
            }

            $status = [
                'code' => 200,
                'status' => 'OK',
                'message' => 'Status Berhasil Diubah',
                'data' => $array_data
            ];
        } catch (QueryException $error) {
            $status = [
                'code' => 500,
                'status' => 'Internal Server Error',
                'message' => $error
            ];
        }
        return $status;
    }

    public function dataTableTarik()
    {
        $query = DB::table($this->view)
            ->select('id_transaksi', 'saldo_transaksi', 'status_transaksi', 'jenis_transaksi', 'created_at', 'nama_users')
            ->orderBy('created_at', 'desc')
            ->where('jenis_transaksi', 3);
        $data_table = Datatables::of($query)
            ->addColumn('action', function ($data) {
                return '<div class="btn-group">
                <a href="' . route('transaksi.tarik.detail') . '?id=' . encrypt($data->id_transaksi) . '" class="btn btn-xs btn-complete"><i class="fa fa-search"></i> Detail</a>
                </div>
                ';
            })->make(true);
        return $data_table;
    }

    public function updateTarik($array_data)
    {
        try {
            self::where($this->primaryKey, $array_data[$this->primaryKey])
                ->update([
                    "status_transaksi" => $array_data['status_transaksi'],
                    'updated_by' => $array_data['updated_by'],
                    'updated_at' => date("Y-m-d H:i:s")
                ]);

            if ($array_data['status_transaksi'] == $this->status_success) {
                $fetch_saldo = DB::table('tbl_rsc_dompet')
                    ->select('id_users', 'saldo_dompet')
                    ->where('id_users', $array_data['created_by'])
                    ->first();
                $saldo_sebelumnya = (int)$fetch_saldo->saldo_dompet;
                $saldo_setelah = $saldo_sebelumnya-(int)$array_data['saldo_transaksi'];
                DB::table('tbl_rsc_dompet')
                    ->where('id_users', $array_data['created_by'])
                    ->update([
                        'saldo_dompet' => $saldo_setelah,
                        'updated_by' => $array_data['updated_by'],
                        'updated_at' => date("Y-m-d H:i:s")
                    ]);
            }

            $status = [
                'code' => 200,
                'status' => 'OK',
                'message' => 'Status Berhasil Diubah',
                'data' => $array_data
            ];
        } catch (QueryException $error) {
            $status = [
                'code' => 500,
                'status' => 'Internal Server Error',
                'message' => $error
            ];
        }
        return $status;
    }

    public function dataTableDonasi()
    {
        $query = DB::table($this->view)
            ->select('id_transaksi', 'saldo_transaksi', 'status_transaksi', 'jenis_transaksi', 'created_at', 'nama_users')
            ->orderBy('created_at', 'desc')
            ->where('jenis_transaksi', 2);
        $data_table = Datatables::of($query)->make(true);
        return $data_table;
    }

    public function updateDonasi($array_data)
    {
        try {
            self::where($this->primaryKey, $array_data[$this->primaryKey])
                ->update([
                    "status_transaksi" => $array_data['status_transaksi'],
                    'updated_by' => $array_data['updated_by'],
                    'updated_at' => date("Y-m-d H:i:s")
                ]);

            if ($array_data['status_transaksi'] == $this->status_success) {
                $fetch_saldo = DB::table('tbl_rsc_dompet')
                    ->select('id_users', 'saldo_dompet')
                    ->where('id_users', $array_data['created_by'])
                    ->first();
                $saldo_sebelumnya = (int)$fetch_saldo->saldo_dompet;
                $saldo_setelah = $saldo_sebelumnya-(int)$array_data['saldo_transaksi'];
                DB::table('tbl_rsc_dompet')
                    ->where('id_users', $array_data['created_by'])
                    ->update([
                        'saldo_dompet' => $saldo_setelah,
                        'updated_by' => $array_data['updated_by'],
                        'updated_at' => date("Y-m-d H:i:s")
                    ]);
            }

            $status = [
                'code' => 200,
                'status' => 'OK',
                'message' => 'Status Berhasil Diubah',
                'data' => $array_data
            ];
        } catch (QueryException $error) {
            $status = [
                'code' => 500,
                'status' => 'Internal Server Error',
                'message' => $error
            ];
        }
        return $status;
    }

    public function autoDonasiUang($request_data)
    {
        $feed_model = new FeedModel();
        $list_donasi = $feed_model->getAutoFeed()['data'];

        $saldo = (int)$request_data['saldo_dompet'];
        $potongan_donasi = array();
        $list_auto = array();

        foreach ($list_donasi as $feed) {
            $sum[] = (int)$feed->min_donasi_feed;
            $array_sum = (int)array_sum($sum);
            if ($array_sum < $saldo) {
                array_push($list_auto, array(
                    'id_feed' => $feed->id_feed,
                    'jenis_transaksi' => 2,
                    'status_transaksi' => 1,
                    'saldo_transaksi' => (int)$feed->min_donasi_feed,
                    'created_by' => $request_data['id_users']
                ));
                array_push($potongan_donasi, (int)$feed->min_donasi_feed);
            } elseif ($array_sum >= $saldo) {
                break;
            } else {
                break;
            }
        }

        $sum_potongan_donasi = array_sum($potongan_donasi);

        try {
            DB::table($this->table)->insert($list_auto);
            /**
             * Update Saldo
             */
            $fetch_saldo = DB::table('tbl_rsc_dompet')
                ->select('id_users', 'saldo_dompet')
                ->where('id_users', $request_data['id_users'])
                ->first();
            $saldo_sebelumnya = (int)$fetch_saldo->saldo_dompet;
            $saldo_setelah = $saldo_sebelumnya-(int)$sum_potongan_donasi;
            DB::table('tbl_rsc_dompet')
                ->where('id_users', $request_data['id_users'])
                ->update([
                    'saldo_dompet' => $saldo_setelah,
                    'updated_by' => $request_data['id_users'],
                    'updated_at' => date("Y-m-d H:i:s")
                ]);

            $status = [
                'code' => 200,
                'status' => 'OK',
                'message' => 'Data Berhasil Dibuat'
            ];
        } catch (QueryException $error) {
            $status = [
                'code' => 500,
                'status' => 'Internal Server Error',
                'message' => $error
            ];
        }
        return $status;
    }

}
