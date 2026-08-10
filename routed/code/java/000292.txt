package com.android.favour.NetworkIO;

import android.content.Context;
import android.view.View;
import android.widget.ImageView;
import android.widget.ProgressBar;

import com.android.favour.R;
import com.bumptech.glide.Glide;
import com.bumptech.glide.Priority;
import com.bumptech.glide.load.resource.drawable.GlideDrawable;
import com.bumptech.glide.request.RequestListener;
import com.bumptech.glide.request.target.Target;

public class ImageServiceClient {

    private Context context;

    public void getImage(String uri, ImageView imgView){
        context = imgView.getContext();
        Glide.with(context)
                .load(uri)
                .dontAnimate()
                .priority(Priority.NORMAL)
                .error(R.drawable.flag)
                .into(imgView);
    }

    public void getImage(final NetworkImageRequest imgRequest){
        context = imgRequest.getImgView().getContext();
        final ImageView imgView = imgRequest.getImgView();
        final ProgressBar progressBar;
        if((progressBar = imgRequest.getLoadingSpinner()) != null) {
            progressBar.setVisibility(View.VISIBLE);
        }
        else if(imgRequest.getLoadingImage() > 0) {
            imgView.setImageResource(imgRequest.getLoadingImage());
        }
        Priority glidePriority = (Priority) imgRequest.getImgPriority();
        Glide.with(context)
            .load(imgRequest.getUri())
            .dontAnimate()
            .priority(Priority.NORMAL)
            .override(Target.SIZE_ORIGINAL, Target.SIZE_ORIGINAL)
            .listener(new RequestListener<String, GlideDrawable>() {

                @Override
                public boolean onException(Exception e, String model, Target<GlideDrawable> target, boolean isFirstResource) {
                    if (progressBar != null) {
                        progressBar.setVisibility(View.GONE);
                    }
                    if (imgRequest.getErrorImage() > 0) {
                        imgView.setImageResource(imgRequest.getErrorImage());
                    }
                    return false;
                }

                @Override
                public boolean onResourceReady(GlideDrawable resource, String
                        model, Target<GlideDrawable> target, boolean isFromMemoryCache,
                                               boolean isFirstResource) {
                    if (progressBar != null) {
                        progressBar.setVisibility(View.GONE);
                    }
                    imgRequest.getImgView().setVisibility(View.VISIBLE);
                    return false;
                }
            })
            .into(imgView);
    }
}
