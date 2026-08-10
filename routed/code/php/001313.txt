 <script type="text/javascript">

 /********************  
  * Id can be hide or show
  * 
	*onload functions
	********************/
	window.onload = start;
	function start () {
		//alert("mickidadi");
		body();
		 
	}
     function body() { 
   var cat= document.getElementById('employerId').style.display = 'none';
   
        }
       function body() { 
   var cat= document.getElementById('employerId').style.display = 'none';
   
        }
    function hidedata() { 
       // alert("Hidde Data");
    var cat= document.getElementById('loaderId').style.display = '';
    var cat= document.getElementById('formId').style.display = 'none';
        }
  </script>
<?php

use yii\helpers\Html;
use kartik\grid\GridView;
use yii\helpers\ArrayHelper;
/* @var $this yii\web\View */
/* @var $searchModel backend\modules\application\models\ApplicationSearch */
/* @var $dataProvider yii\data\ActiveDataProvider */

$this->title = 'List of Application ';
$this->params['breadcrumbs'][] = $this->title;
 
?>

<div class="application-index">
 <div class="panel panel-info">
        <div class="panel-heading">
<?= Html::encode($this->title) ?>
        </div>
        <div class="panel-body">
         <div id="loaderId" style="display:none">
 
  <?php echo Html::img('@web/image/loader/loader2.gif') ?>  
     </div>   
            <div  id="formId">
      <p>
        <?= Html::a('Click to check Eligibility', ['check-compliance'], ['class' => 'btn btn-success','onclick'=>"return hidedata()"]) ?>
      </p>
    
    <?= GridView::widget([
        'dataProvider' => $dataProvider,
        'filterModel' => $searchModel,
        'columns' => [
            ['class' => 'yii\grid\SerialColumn'],
               [
                'class' => 'kartik\grid\ExpandRowColumn',
                'value' => function ($model, $key, $index, $column) {
                    return GridView::ROW_COLLAPSED;
                },
                'allowBatchToggle' => true,
                'detail' => function ($model) {
                  return $this->render('application-compliance-view',['model'=>$model]);  
                },
                'detailOptions' => [
                    'class' => 'kv-state-enable',
                ],
                ],
            //'application_id',
           // 'applicant_id',
                        
            [
                     'attribute' => 'firstName',
                        'label'=>"First Name",
                        'vAlign' => 'middle',
                       // 'width' => '200px',
                        'value' => function ($model) {
                            return $model->applicant->user->firstname;
                        },
                    ],
                    [
                     'attribute' => 'surname',
                         'label'=>"Last Name",
                        'vAlign' => 'middle',
                         
                       // 'width' => '200px',
                        'value' => function ($model) {
                            return $model->applicant->user->surname;
                        },
                    ],
                    [
                     'attribute' => 'f4indexno',
                        'label'=>"f4 Index #",
                        'vAlign' => 'middle',
                       // 'width' => '200px',
                        'value' => function ($model) {
                            return $model->applicant->f4indexno;
                        },
                    ],
//                 [
//                     'attribute' => 'application_study_year',
//                       // 'label'=>"f4 Index #",
//                        'vAlign' => 'middle',
//                        'width' => '200px',
//                        'value' => function ($model) {
//                            return $model->application_study_year;
//                        },
//                       'filterType' => GridView::FILTER_SELECT2,
//                        'filter' =>[1=>1,2=>2,3=>3,4=>4,5=>5],
//                        'filterWidgetOptions' => [
//                            'pluginOptions' => ['allowClear' => true],
//                        ],
//                        'filterInputOptions' => ['placeholder' => 'Search'],
//                        'format' => 'raw'
//                    ],
//                     [
//                        'attribute' => 'academic_year_id',
//                        'vAlign' => 'middle',
//                       // 'width' => '200px',
//                        'value' => function ($model) {
//                            return $model->academicYear->academic_year;
//                        },
//                        'filterType' => GridView::FILTER_SELECT2,
//                        'filter' => ArrayHelper::map(\common\models\AcademicYear::find()->where("is_current=1")->asArray()->all(), 'academic_year_id', 'academic_year'),
//                        'filterWidgetOptions' => [
//                            'pluginOptions' => ['allowClear' => true],
//                        ],
//                        'filterInputOptions' => ['placeholder' => 'Search'],
//                        'format' => 'raw'
//                    ],
           // 'academic_year_id',
           // 'bill_number',
           // 'control_number',
            // 'receipt_number',
            // 'amount_paid',
            // 'pay_phone_number',
            // 'date_bill_generated',
            // 'date_control_received',
            // 'date_receipt_received',
            // 'programme_id',
            // 'application_study_year',
            // 'current_study_year',
            // 'applicant_category_id',
            // 'bank_account_number',
            // 'bank_account_name',
            // 'bank_id',
            // 'bank_branch_name',
            // 'submitted',
             //'verification_status',
           //  'needness',
//            // 'allocation_status',
//                   [
//                        'attribute' => 'allocation_status',
//                        'vAlign' => 'middle',
//                        'width' => '200px',
//                        'value' => function ($model) {
//                            return $model->academicYear->academic_year;
//                        },
//                        'filterType' => GridView::FILTER_SELECT2,
//                        'filter' => ArrayHelper::map(\common\models\AcademicYear::find()->where("is_current=1")->asArray()->all(), 'academic_year_id', 'academic_year'),
//                        'filterWidgetOptions' => [
//                            'pluginOptions' => ['allowClear' => true],
//                        ],
//                        'filterInputOptions' => ['placeholder' => 'Search'],
//                        'format' => 'raw'
//                    ],
            // 'allocation_comment',
            // 'student_status',
            // 'created_at',

           // ['class' => 'yii\grid\ActionColumn'],
        ],
        'hover' => true,
        'condensed' => true,
        'floatHeader' => true,
    ]); ?>
</div>
 </div>
</div>
</div>