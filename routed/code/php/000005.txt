<?php

namespace App\Http\Livewire;

use App\Models\Post;
use Livewire\Component;

class Posts extends Component
{
    public $posts, $title, $body, $post_id;
    public $updatedMode = false;

    public function render()
    {
        $this->posts = Post::all();

        return view('livewire.posts');
    }

    /**
     * Save a post
     */
    public function store()
    {
        $validData = $this->validate([
            'title' => 'required',
            'body' => 'required',
        ]);

        Post::create($validData);

        \session()->flash('success','Post created successfully.');

        $this->resetInputFields();
    }

    /**
     * Set values for edit form
     */
    public function edit($id)
    {
        $post = Post::findOrFail($id);
        $this->post_id = $post->id;
        $this->title = $post->title;
        $this->body = $post->body;

        $this->updatedMode = true;
    }

    public function update()
    {
        $this->validate([
            'title' => 'required',
            'body' => 'required',
        ]);

        $post = Post::find($this->post_id);
        $post->update([
            'title' => $this->title,
            'body' => $this->body
        ]);

        $this->updatedMode = false;

        \session()->flash('success','Post updated successfully.');

        $this->resetInputFields();
    }

    /**
     * Cancel button on edit form
     */
    public function cancel()
    {
        $this->updatedMode = false;
        $this->resetInputFields();
    }

    public function delete($id)
    {
        Post::find($id)->delete();

        \session()->flash('success','Post deleted Successfully');
    }

    /**
     * Reset form fields
     */
    private function resetInputFields()
    {
        $this->title = '';
        $this->body = '';
    }
}
