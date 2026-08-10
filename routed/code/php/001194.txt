<?php

namespace Tonic\Console\Commands;

use Tonic\Role;

use Illuminate\Console\Command;

class ListRoles extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'list:roles';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'List all roles from database';

    /**
     * Create a new command instance.
     *
     * @return void
     */
    public function __construct()
    {
        parent::__construct();
    }

    /**
     * Execute the console command.
     *
     * @return mixed
     */
    public function handle()
    {
        if (! $roles = Role::all()) {
            $this->info('There are no roles. Create some with "create:role {role}"');
            return;
        }

        foreach ($roles as $role) {
            $this->info('- ' . $role->name);
        }
    }
}
