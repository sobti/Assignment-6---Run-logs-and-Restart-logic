package ch.zhaw.securitylab.DIMBA.activity.stock;

import android.app.TaskStackBuilder;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.ListView;

import ch.zhaw.securitylab.DIMBA.DIMBA;
import ch.zhaw.securitylab.DIMBA.R;
import ch.zhaw.securitylab.DIMBA.activity.ActivityDIMBAAbstract;
import ch.zhaw.securitylab.DIMBA.activity.ToolbarMode;

public class ActivityAuthStockList extends ActivityDIMBAAbstract implements AdapterView.OnItemClickListener {

    private SharedPreferences defaultPreferences;
    private ListView stockListView;
    private ListView forexListView;
    private ListView forexValuesView;
    private ListView commodityListView;
    private String[] stockNames;
    private String[] forexNames;
    private String[] commodityNames;

    public ActivityAuthStockList() {
        super(R.layout.activity_auth_stock_list, ToolbarMode.NAV_AUTH, R.id.nav_go_Stock);
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        defaultPreferences = PreferenceManager.getDefaultSharedPreferences(DIMBA.get());

        runOnUiThread(() -> {
            forexNames = new String[]{"USD/CHF                                                      + 1.2%",
                                      "CHF/EUR                                                      + 0.1%",
                                      "EUR/USD                                                      - 0.7%"};
            addList(forexListView,forexNames, R.id.ForexList);

            commodityNames = new String[]{
                                      "Crude Oil                                                       - 0.1%",
                                      "Gold                                                                + 0.5%",
                                      "Gas                                                                 + 4.5%"};
            addList(commodityListView,commodityNames, R.id.CommodityList);

            stockNames = new String[]{"APPL                                                               + 0.3%",
                                      "GOOGL                                                           + 0.3%",
                                      "MSFT                                                              + 0.8%"};
            addList(stockListView,stockNames, R.id.StockList);
        });
    }

    public void addList(ListView lv, String[] list, int id) {
        lv = findViewById(id);
        ArrayAdapter<String> stockAdapter = new ArrayAdapter<>(this, android.R.layout.simple_list_item_1, list);
        lv.setAdapter(stockAdapter);
        lv.setOnItemClickListener(this);
    }

    @Override
    public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
        Class clazz = ActivityAuthStock.class;

        TaskStackBuilder.create(this)
                .addParentStack(clazz)
                .addNextIntent(new Intent(this, clazz))
                .startActivities();
    }
}
