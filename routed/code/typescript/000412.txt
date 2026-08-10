import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { AlbumEntity } from '../entities/album.entity';
import { Repository } from 'typeorm';
import { AlbumDto } from '../dtos/album.dto';
import { SongEntity } from '../entities/song.entity';
import { MusicGenreEntity } from '../entities/musicgenre.entity';
import { BandEntity } from '../entities/band.entity';

@Injectable()
export class AlbumService {

    constructor(

    @InjectRepository(AlbumEntity)
    private readonly albumRepository: Repository<AlbumEntity>,

    @InjectRepository(SongEntity)
    private readonly songRepository: Repository<SongEntity>,

    @InjectRepository(MusicGenreEntity)
    private readonly mgenreRepository: Repository<MusicGenreEntity>,

    @InjectRepository(BandEntity)
    private readonly bandRepository: Repository<BandEntity>
    ){

    }
    

     findAllAlbum(limit: number, offset: number){
        return this.albumRepository.find({skip: offset,
            take: limit,relations:['songsAlbum','bandAlbums','artisteAlbums','musicgenre']});
    }

    async findOneAlbum(albumId: string){
        const album = await this.albumRepository.findOne(+albumId, {relations:['songsAlbum','bandAlbums','artisteAlbums','musicgenre']});
        if(!album)
            return null;
        return album;
    }

    async updateAlbum(albumId: string, albumDto: AlbumDto){
        let album = await this.albumRepository.findOne(+albumId, {relations:['songsAlbum','bandAlbums','artisteAlbums','musicgenre']});
        if(!album)
            return null;
        await this.albumRepository.update(albumId,albumDto);
        album = await this.albumRepository.findOne(+albumId, {relations:['songsAlbum','bandAlbums','artisteAlbums','musicgenre']});
        return {updatedId: albumId, Album: album};
    }

    async SongAlbum(albumId: string, songId: string){
        const album = await this.albumRepository.findOne(+albumId, {relations:['songsAlbum','bandAlbums','artisteAlbums','musicgenre']});        
        if(!album)
            return null;
        const song = await this.songRepository.findOne(+songId);
        if(!song)
            return null;
        album.songsAlbum.push(song);    
        await this.albumRepository.save(album);    
        return this.albumRepository.findOne(+albumId, {relations:['songsAlbum','bandAlbums','artisteAlbums','musicgenre']});
    }

    async DeleteSongAlbum(albumId: string, songId: string){
        const album = await this.albumRepository.findOne(+albumId, {relations:['songsAlbum','bandAlbums','artisteAlbums','musicgenre']});        
        if(!album)
            return null;        
        if(!album.songsAlbum)
            return null;
            for(let i=0;i< album.songsAlbum.length;i++){
                if(album.songsAlbum[i].songId === +songId)
                album.songsAlbum.splice(i,1);
            }    
        await this.albumRepository.save(album);    
        return this.albumRepository.findOne(+albumId, {relations:['songsAlbum','bandAlbums','artisteAlbums','musicgenre']});
    }

    async GenreAlbum(albumId: string, mgenreId: string){
        const album = await this.albumRepository.findOne(+albumId, {relations:['songsAlbum','bandAlbums','artisteAlbums','musicgenre']});        
        if(!album)
            return null;
        const mgenre = await this.mgenreRepository.findOne(+mgenreId);
        if(!mgenre)
            return null;
        album.musicgenre=mgenre;    
        await this.albumRepository.save(album);    
        return this.albumRepository.findOne(+albumId, {relations:['songsAlbum','bandAlbums','artisteAlbums','musicgenre']});
    }

    async DeleteGenreAlbum(albumId: string, mgenreId: string){
        const album = await this.albumRepository.findOne(+albumId, {relations:['songsAlbum','bandAlbums','artisteAlbums','musicgenre']});        
        if(!album)
            return null;        
        if(!album.musicgenre)
            return null;            
            if(album.musicgenre.musicGenreId === +mgenreId)
                album.musicgenre=null;
        await this.albumRepository.save(album);    
        return this.albumRepository.findOne(+albumId, {relations:['songsAlbum','bandAlbums','artisteAlbums','musicgenre']});
    }

    async BandAlbum(albumId: string, bandId: string){
        const album = await this.albumRepository.findOne(+albumId, {relations:['songsAlbum','bandAlbums','artisteAlbums','musicgenre']});        
        if(!album)
            return null;
        const mgenre = await this.bandRepository.findOne(+bandId);
        if(!mgenre)
            return null;
        album.bandAlbums.push(mgenre);    
        await this.albumRepository.save(album);    
        return this.albumRepository.findOne(+albumId, {relations:['songsAlbum','bandAlbums','artisteAlbums','musicgenre']});
    }

    async DeleteBandAlbum(albumId: string, bandId: string){
        const album = await this.albumRepository.findOne(+albumId, {relations:['songsAlbum','bandAlbums','artisteAlbums','musicgenre']});        
        if(!album)
            return null;        
        if(!album.bandAlbums)
            return null;
            for(let i=0;i< album.bandAlbums.length;i++){
                if(album.bandAlbums[i].bandId === +bandId)
                album.bandAlbums.splice(i,1);
            }    
        await this.albumRepository.save(album);    
        return this.albumRepository.findOne(+albumId, {relations:['songsAlbum','bandAlbums','artisteAlbums','musicgenre']});
    }

    async removeAlbum(albumId: string){
        const album = await this.albumRepository.findOne(+albumId);
        if(!album)
            return null;
        await this.albumRepository.delete(+albumId);
        return {deletedId: albumId, nbAlbum: await this.albumRepository.findAndCount.length};
    }

    async createAlbum(albumDto: AlbumDto){        
        const album = await this.albumRepository.save(albumDto);
        return album;
    }
}
