<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Groomer extends CI_Controller {

	public function __construct()
	{
		parent::__construct();
		$this->load->model('groomer_model', 'groomer');
	}

	public function index()
	{
		$data = array(
			'title'	=> 'Data Groomer',
			'data'	=> $this->groomer->list(),
			'content'	=> 'admin/groomer/v_content'
		);
		$this->load->view('admin/layout/v_wrapper', $data, FALSE);
	}

	public function add()
	{
		$this->form_validation->set_rules('nama', 'Nama groomer', 'required',
			array( 'required'  => '%s harus diisi!'));

		if ($this->form_validation->run()) 
		{
			$i = $this->input;
			$data = array(
				'nama_groomer'	=> $i->post('nama'),
				'jk_groomer'		=> $i->post('jk'),
				'telepon_groomer'		=> $i->post('telepon'),
				'alamat_groomer'		=> $i->post('alamat')
			);
			$this->db->insert('groomer',$data);
			$this->session->set_flashdata('sukses', '<i class="fa fa-info-circle"></i> Groomer berhasil ditambahkan!');
			redirect(base_url('admin/groomer'), 'refresh');
		} 
		$data = array(
			'title'	=> 'Tambah Groomer',
			'content'	=> 'admin/groomer/v_add'
		);
		$this->load->view('admin/layout/v_wrapper', $data, FALSE);
	}

	public function edit($id_groomer)
	{
		$detail = $this->groomer->detail($id_groomer);

		$this->form_validation->set_rules('nama', 'Nama groomer', 'required',
			array( 'required'  => '%s harus diisi!'));

		if ($this->form_validation->run()) 
		{
			$i = $this->input;
			$data = array(
				'id_groomer'	=> $id_groomer,
				'nama_groomer'	=> $i->post('nama'),
				'jk_groomer'		=> $i->post('jk'),
				'telepon_groomer'		=> $i->post('telepon'),
				'alamat_groomer'		=> $i->post('alamat')
			);
			$this->groomer->edit($data);
			$this->session->set_flashdata('sukses', '<i class="fa fa-info-circle"></i> Groomer berhasil diubah!');
			redirect(base_url('admin/groomer'), 'refresh');
		} 
		$data = array(
			'title'	=> 'Tambah Groomer',
			'detail'	=> $detail,
			'content'	=> 'admin/groomer/v_edit'
		);
		$this->load->view('admin/layout/v_wrapper', $data, FALSE);
	}

	public function delete($id_groomer)
	{
		$i = $this->input;
		$data = array(
			'id_groomer'	=> $id_groomer
		);
		$this->groomer->delete($data);
		$this->session->set_flashdata('sukses', '<i class="fa fa-info-circle"></i> Groomer berhasil dihapus!');
		redirect(base_url('admin/groomer'), 'refresh');
	}

}

/* End of file Groomer.php */
/* Location: ./application/controllers/admin/Groomer.php */