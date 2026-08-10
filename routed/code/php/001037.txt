@extends('layouts.backend')

@section('title', 'Add New Media')

@section('content')
    <div class="container-fluid">
        <div class="row">
            <div class="col-lg-12">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">{{ __('Edit Media') }}</h3>
                        <div class="card-tools">
                            <a class="btn btn-info"
                               href="{{ route('admin.media.index') }}">{{ __('Media Manager') }}</a>
                        </div>
                    </div>
                    <div class="card-body">
                        {{ Form::model($medium,['route'=>['admin.media.update',$medium->id], 'class'=> 'dropzone', 'id' => 'addImages', 'files'=>true]) }}
                        @method('PUT')
                        <div class="form-group">
                            {{ Form::label('name', __('Name')) }}
                            {{ Form::text('name', null , ['class'=> $errors->has('name') ? 'form-control is-invalid' : 'form-control']) }}
                            <span class="invalid-feedback">{{ $errors->first('name') }}</span>
                        </div>
                        <div class="form-group row">
                            <div class="col-lg-3">
                                <div class="input-group mb-3">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">{{ __('Width') }}</span>
                                    </div>
                                    {{ Form::number('width', $medium->width, ['class'=>$errors->has('width') ? 'form-control is-invalid' : 'form-control','id'=> 'width','data-width'=> $medium->width]) }}
                                    <div class="input-group-append">
                                        <span class="input-group-text">{{ __('px') }}</span>
                                    </div>
                                </div>

                                <span class="invalid-feedback">{{ $errors->first('width') }}</span>
                            </div>
                            <div class="col-lg-3">
                                <div class="input-group mb-3">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">{{ __('Height') }}</span>
                                    </div>
                                    {{ Form::number('height', $medium->height, ['class'=>$errors->has('height') ? 'form-control is-invalid' : 'form-control','id'=> 'height','data-height'=> $medium->height]) }}
                                    <div class="input-group-append">
                                        <span class="input-group-text">{{ __('px') }}</span>
                                    </div>
                                </div>
                                <span class="invalid-feedback">{{ $errors->first('height') }}</span>
                            </div>
                            <div class="col-lg-3">
                                <div class="input-group mb-3">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">{{ __('X') }}</span>
                                    </div>
                                    {{ Form::number('x', null, ['class'=>$errors->has('x') ? 'form-control is-invalid' : 'form-control','id'=> 'dataX']) }}
                                    <div class="input-group-append">
                                        <span class="input-group-text">{{ __('px') }}</span>
                                    </div>
                                </div>

                                <span class="invalid-feedback">{{ $errors->first('x') }}</span>
                            </div>
                            <div class="col-lg-3">
                                <div class="input-group mb-3">
                                    <div class="input-group-prepend">
                                        <span class="input-group-text">{{ __('Y') }}</span>
                                    </div>
                                    {{ Form::number('y', null, ['class'=>$errors->has('y') ? 'form-control is-invalid' : 'form-control','id'=> 'dataY']) }}
                                    <div class="input-group-append">
                                        <span class="input-group-text">{{ __('px') }}</span>
                                    </div>
                                </div>
                                <span class="invalid-feedback">{{ $errors->first('y') }}</span>
                            </div>
                        </div>

                        <div class="form-group">
                            <img width="100%" id="medium-image" src="{{ asset('storage/images/media/'.$medium->path) }}"
                                 alt="Image">
                        </div>
                        <div class="btn-group pull-right">
                            <button id="clear" class="btn btn-sm btn-primary">{{ __('Clear') }}</button>
                        </div>

                        <div class="form-group mt-3">
                            <label>
                                <input type="checkbox" class="minimal" name="save_as_new" value="1"> {{ __('Save as new') }}
                            </label>
                        </div>

                        <div class="form-group mt-3">
                            {{ Form::submit(__('Update'), ['class'=>'btn btn-success']) }}
                        </div>
                        {{ Form::close() }}
                    </div>
                </div>
            </div>
        </div>
    </div>

@endsection

@section('style')
    <link rel="stylesheet" href="{{ asset('vendor/cropper/cropper.min.css') }}">
    <link rel="stylesheet" href="{{ asset('vendor/iCheck/all.css') }}">
@endsection
@section('script')
    <script src="{{ asset('vendor/cropper/cropper.min.js') }}"></script>
    <script src="{{ asset('vendor/iCheck/icheck.min.js') }}"></script>
    <script>
        $(document).ready(function () {
            $('#file').on('change', function (e) {
                var fileName = e.target.files[0].name;
                console.log(e.target.files);
                $('.custom-file-label').html(fileName);
            });

            var image = $('#medium-image');
            var dataWidth = $('#width');
            var dataHeight = $('#height');
            var dataX = $('#dataX');
            var dataY = $('#dataY');
            var cropper = image.cropper({
                viewMode: 3,
                autoCrop: false,
                zoomable: false,
                checkCrossOrigin: false,
                crop: function (e) {
                    dataX.val(Math.round(e.detail.x));
                    dataY.val(Math.round(e.detail.y));
                    dataHeight.val(Math.round(e.detail.height));
                    dataWidth.val(Math.round(e.detail.width));
                }
            });

            $(document).on('click', '#clear', function (e) {
                e.preventDefault();
                image.cropper('clear');
                dataHeight.val(Math.round(dataHeight.data('height')));
                dataWidth.val(Math.round(dataWidth.data('width')));
            });

            $('input[type="checkbox"].minimal, input[type="radio"].minimal').iCheck({
                checkboxClass: 'icheckbox_minimal-blue',
                radioClass   : 'iradio_minimal-blue'
            });

        });
    </script>
@endsection